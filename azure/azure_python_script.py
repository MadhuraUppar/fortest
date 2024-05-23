import subprocess
import pandas as pd
import snowflake.connector
import sys
import re

def azure_users(azure_username, azure_password, azure_object_id):
    try:
        # PowerShell script block to connect to Azure and fetch user details
        script_block = f""" 
            $User = '{azure_username}'
            $TenantId = "0101c982-42b5-4932-8d76-28b81fc704c8"
            $PWord = ConvertTo-SecureString -String '{azure_password}' -AsPlainText -Force
            $Credentials = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord
            $nomsg=Connect-AzAccount -Credential $Credentials -TenantId $TenantId -AuthScope 'https://graph.microsoft.com'
            $contextForMSGraphToken = [Microsoft.Azure.Commands.Common.Authentication.Abstractions.AzureRmProfileProvider]::Instance.Profile.DefaultContext
            $newBearerAccessTokenRequest = [Microsoft.Azure.Commands.Common.Authentication.AzureSession]::Instance.AuthenticationFactory.Authenticate($contextForMSGraphToken.Account, $contextForMSGraphToken.Environment, $contextForMSGraphToken.Tenant.id.ToString(), $null, [Microsoft.Azure.Commands.Common.Authentication.ShowDialog]::Never, $null, 'https://graph.microsoft.com')
            $AccessToken = $newBearerAccessTokenRequest.AccessToken
            $SecureAccessToken = ConvertTo-SecureString -String $AccessToken -AsPlainText -Force
            Connect-MgGraph -AccessToken $SecureAccessToken -NoWelcome
            Get-MgGroupMember -GroupId {azure_object_id} -all | ForEach-Object {{ Get-MgUser -UserId $_.Id }} | Select-Object DisplayName, UserPrincipalName, GivenName, Surname, Department, JobTitle   
            """
        script_block_1 = f"""
            $password = ConvertTo-SecureString '{azure_password}' -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential('{azure_username}', $password)
            Connect-AzureAD -Credential $cred
            Get-AzureADGroupMember -ObjectId {azure_object_id} -All $true |
                ForEach-Object {{ Get-AzureADUser -ObjectId $_.ObjectId }} |
                Select-Object DisplayName, UserPrincipalName, GivenName, Surname, Department, JobTitle
        """ 
        # Run PowerShell script using subprocess
        result = subprocess.run(
            [r"C:\Program Files\PowerShell\7\pwsh.EXE", "-Command", f"& {{{script_block}}}"],
            capture_output=True, text=True)
        
        # Check if the PowerShell script execution was successful
        if result.returncode != 0:
            print("Error connecting to Azure AD. Return code not equal to 0.")
            print("Error:", result.stderr)
            return 
        if result.stderr:
            print("Error connecting to Azure AD. Error output , result.stderr is :", result.stderr)
            return 
        else:
            # Process the output and create a DataFrame
            output = result.stdout
            print("result.stdout is ")
            print(output)
            print(result)
            # output format containing escape characters like '\x1b[32;1m' to remove this used re.compile
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            output = ansi_escape.sub('', output)
            lines = [
                line.strip() for line in output.strip().split("\n") if line.strip()
            ]
            data = {}
            for i in range(0, len(lines), 6):
                display_name = lines[i].split(":")[1].strip()
                user_principal_name = lines[i + 1].split(":")[1].strip()
                firstname = lines[i + 2].split(":")[1].strip()
                lastname = lines[i + 3].split(":")[1].strip()
                department = lines[i + 4].split(":")[1].strip()
                job_title = lines[i + 5].split(":")[1].strip()
                data.setdefault("DisplayName", []).append(display_name)
                data.setdefault("UserPrincipalName", []).append(user_principal_name)
                data.setdefault("FirstName", []).append(firstname)
                data.setdefault("LastName", []).append(lastname)
                data.setdefault("Department", []).append(department)
                data.setdefault("JobTitle", []).append(job_title)
            df = pd.DataFrame(data)
        
        return df

    except subprocess.CalledProcessError as e:
        print("Error connecting to Azure AD:", e)
        print("Error output:", e.output)
        sys.exit(1)
    except Exception as e:
        print("An unexpected error occurred:", e)
        sys.exit(1)


if __name__ == "__main__":
    # Fetch Azure users and insert into Snowflake
    print(sys.argv[2], sys.argv[3], sys.argv[4])
    df = azure_users(sys.argv[2], sys.argv[3], sys.argv[4])
    print(df)
    

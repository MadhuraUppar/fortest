# Set execution policy (for testing)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Define variables
$User = 'svc_snowflake@invitationhomes.com'
$PWord = ConvertTo-SecureString -String 'szU12ts89W' -AsPlainText -Force
$TenantId = 'a9206aee-bab2-4a84-9b62-1be92b7f18c0'
$Credentials = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $User, $PWord

try {
    # Attempt to connect to Azure account
    $nomsg = Connect-AzAccount -Credential $Credentials -TenantId $TenantId -AuthScope 'https://graph.microsoft.com'

    # Check if connection was successful
    if ($nomsg) {
        Write-Host "Connected to Azure account successfully."
        
        # Get access token for Microsoft Graph
        $contextForMSGraphToken = [Microsoft.Azure.Commands.Common.Authentication.Abstractions.AzureRmProfileProvider]::Instance.Profile.DefaultContext
        $newBearerAccessTokenRequest = [Microsoft.Azure.Commands.Common.Authentication.AzureSession]::Instance.AuthenticationFactory.Authenticate($contextForMSGraphToken.Account, $contextForMSGraphToken.Environment, $TenantId, $null, [Microsoft.Azure.Commands.Common.Authentication.ShowDialog]::Never, $null, 'https://graph.microsoft.com')
        
        # Check if access token was obtained
        if ($newBearerAccessTokenRequest) {
            $AccessToken = $newBearerAccessTokenRequest.AccessToken
            $SecureAccessToken = ConvertTo-SecureString -String $AccessToken -AsPlainText -Force
            
            # Connect to Microsoft Graph
            Connect-MgGraph -AccessToken $SecureAccessToken -NoWelcome
            
            # Retrieve group members
            Get-MgGroupMember -GroupId {azure_object_id} -all | ForEach-Object {
                Get-MgUser -UserId $_.Id
            } | Select-Object DisplayName, UserPrincipalName, GivenName, Surname, Department, JobTitle   
        } else {
            Write-Host "Failed to obtain access token for Microsoft Graph."
        }
    } else {
        Write-Host "Failed to connect to Azure account."
    }
} catch {
    Write-Host "Error occurred: $_"
}

#. script to run the submit_v7_experiments.py script in RFT lab, with auth and env setup. 

# Resources Variables
$envName = "Build@lab.LabInstance.Id"    
$tenantId   = "@lab.CloudSubscription.App"
$appId      = "@lab.CloudSubscription.AppId"
$appSecret  = "@lab.CloudSubscription.AppSecret"
$subId      = "@lab.CloudSubscription.Id"
$secureSecret = ConvertTo-SecureString $appSecret -AsPlainText -Force
$spCredential = New-Object System.Management.Automation.PSCredential($appId, $secureSecret)
$resourceGroup = "@lab.CloudResourceGroup(ResourceGroup1).Name"
$location = "@lab.CloudResourceGroup(ResourceGroup1).Location"

$subscriptionId     = "@lab.CloudSubscription.Id"
$userPrincipalName  = "@lab.CloudPortalCredential(User1).Username"

# Authenticate FIRST, before any Az cmdlets
Connect-AzAccount -ServicePrincipal -Credential $spCredential -TenantId $tenantId -Subscription $subId
Set-AzContext -Subscription $subId -Tenant $tenantId

# Now safe to call Az cmdlets
$azureUserId = (Get-AzADUser -UserPrincipalName $userPrincipalName).Id

# Authenticate Azure CLI separately (az CLI has its own auth context)
az login --service-principal -u $appId -p $appSecret --tenant $tenantId 2>&1 | Out-Null
az account set --subscription $subId 2>&1 | Out-Null

$labRoot = "C:\Users\LabUser\Downloads\Build26-LAB521-main"
$labRequirements = "C:\Users\LabUser\Downloads\Build26-LAB521-main\src\requirements.txt"
$labScript = "C:\Users\LabUser\Downloads\Build26-LAB521-main\src\scripts\submit_v7_experiments.py"

# Find AIServices or OpenAI account in the resource group
$aiAccounts = az cognitiveservices account list `
  --resource-group $resourceGroup `
  --query "[?kind=='AIServices' || kind=='OpenAI'].[name]" -o tsv

if (-not $aiAccounts) {
    Write-Error "No AIServices or OpenAI accounts found in resource group '$resourceGroup'."
    exit 1
}
Write-Host "az account list result: $aiAccounts"

# Take the first account (or only one)
$selectedName = ($aiAccounts -split "`n")[0].Trim()
Write-Host "Selected account: $selectedName"

$endpoint = az cognitiveservices account show `
  --name $selectedName `
  --resource-group $resourceGroup `
  --query properties.endpoint -o tsv
Write-Host "Endpoint: $endpoint"

$apiKey = az cognitiveservices account keys list `
  --name $selectedName `
  --resource-group $resourceGroup `
  --query key1 -o tsv
Write-Host "API key retrieved: $($apiKey.Length) chars"

if (-not $endpoint -or -not $apiKey) {
    Write-Error "Failed to retrieve endpoint or API key from account '$selectedName'."
    exit 1
}

# Set as environment variables for the current process
$env:AZURE_OPENAI_ENDPOINT = $endpoint
$env:AZURE_OPENAI_API_KEY = $apiKey
Write-Host "Environment variables set"

# --- Step 2: Install deps and run the script ---
Write-Host "Installing pip..."
python -m ensurepip --upgrade 2>&1 | Out-Null
Write-Host "Installing requirements..."
python -m pip install -r "$labRequirements" 2>&1 | Out-Null
Write-Host "Running submit_v7_experiments.py..."

python "$labScript"
from __future__ import annotations

import json
from pathlib import Path


def build_azure_powershell_pairs() -> list[dict[str, str]]:
    """Return a curated set of instruction→PowerShell pairs for Azure admin tasks.

    Notes
    -----
    - These examples are written directly (simulating an LLM's output) to avoid
      any external API dependency during dataset generation.
    - Commands primarily use the Az PowerShell module. Some directory or identity
      tasks use the AzureAD module where appropriate.
    - Resource names, locations, and identifiers are examples; adjust to your environment
      if you plan to execute them.
    """

    pairs: list[dict[str, str]] = [
        {
            "instruction": "Find all virtual machines in the 'prod-rg' resource group.",
            "output": "Get-AzVM -ResourceGroupName 'prod-rg'",
        },
        {
            "instruction": "Create a new resource group named 'dev-testing-rg' in the 'East US' location.",
            "output": "New-AzResourceGroup -Name 'dev-testing-rg' -Location 'East US'",
        },
        {
            "instruction": "Start the virtual machine 'web-01' in the 'prod-rg' resource group.",
            "output": "Start-AzVM -Name 'web-01' -ResourceGroupName 'prod-rg'",
        },
        {
            "instruction": "Stop and deallocate the virtual machine 'web-01' in 'prod-rg'.",
            "output": "Stop-AzVM -Name 'web-01' -ResourceGroupName 'prod-rg' -Force",
        },
        {
            "instruction": "Restart the virtual machine 'sql-01' in 'data-rg'.",
            "output": "Restart-AzVM -Name 'sql-01' -ResourceGroupName 'data-rg'",
        },
        {
            "instruction": "Resize the VM 'compute-01' in 'ops-rg' to size 'Standard_D4s_v5'.",
            "output": (
                "$vm = Get-AzVM -Name 'compute-01' -ResourceGroupName 'ops-rg'\n"
                "$vm.HardwareProfile.VmSize = 'Standard_D4s_v5'\n"
                "Update-AzVM -ResourceGroupName 'ops-rg' -VM $vm"
            ),
        },
        {
            "instruction": "Create a StorageV2 account named 'stdevlogs1234' in 'eastus2' with Standard_LRS in 'dev-rg'.",
            "output": (
                "New-AzStorageAccount -ResourceGroupName 'dev-rg' -Name 'stdevlogs1234' "
                "-Location 'eastus2' -SkuName 'Standard_LRS' -Kind 'StorageV2'"
            ),
        },
        {
            "instruction": "Create a private blob container 'logs' on the storage account 'stdevlogs1234' in 'dev-rg'.",
            "output": (
                "$ctx = (Get-AzStorageAccount -ResourceGroupName 'dev-rg' -Name 'stdevlogs1234').Context\n"
                "New-AzStorageContainer -Name 'logs' -Context $ctx -Permission Off"
            ),
        },
        {
            "instruction": "Upload the file './web.log' to the 'logs' container as 'web.log' using the 'stdevlogs1234' storage account in 'dev-rg'.",
            "output": (
                "$ctx = (Get-AzStorageAccount -ResourceGroupName 'dev-rg' -Name 'stdevlogs1234').Context\n"
                "Set-AzStorageBlobContent -File './web.log' -Container 'logs' -Blob 'web.log' -Context $ctx"
            ),
        },
        {
            "instruction": "Delete the resource group 'temp-rg'.",
            "output": "Remove-AzResourceGroup -Name 'temp-rg' -Force",
        },
        {
            "instruction": "Add or update the tag 'env=prod' on all resources in 'prod-rg'.",
            "output": (
                "Get-AzResource -ResourceGroupName 'prod-rg' | ForEach-Object { "
                "Update-AzTag -ResourceId $_.ResourceId -Operation Merge -Tag @{ env = 'prod' } }"
            ),
        },
        {
            "instruction": "Assign the 'Reader' role on resource group 'prod-rg' to user 'alice@contoso.com'.",
            "output": (
                "New-AzRoleAssignment -SignInName 'alice@contoso.com' -RoleDefinitionName 'Reader' "
                "-ResourceGroupName 'prod-rg'"
            ),
        },
        {
            "instruction": "Create a new Azure AD user 'John Doe' with UPN 'john.doe@contoso.com' and require password change on first login.",
            "output": (
                "New-AzureADUser -DisplayName 'John Doe' -UserPrincipalName 'john.doe@contoso.com' "
                "-AccountEnabled $true -MailNickname 'johndoe' -PasswordProfile @{ "
                "ForceChangePasswordNextLogin = $true; Password = 'Pass@w0rd!' }"
            ),
        },
        {
            "instruction": "List resource groups in the 'eastus' region.",
            "output": "Get-AzResourceGroup | Where-Object { $_.Location -eq 'eastus' }",
        },
        {
            "instruction": "Create a virtual network 'vnet-hub' with address space '10.0.0.0/16' and a subnet 'snet-apps' '10.0.1.0/24' in 'network-rg' located in 'eastus'.",
            "output": (
                "$subnet = New-AzVirtualNetworkSubnetConfig -Name 'snet-apps' -AddressPrefix '10.0.1.0/24'\n"
                "New-AzVirtualNetwork -Name 'vnet-hub' -ResourceGroupName 'network-rg' -Location 'eastus' "
                "-AddressPrefix '10.0.0.0/16' -Subnet $subnet"
            ),
        },
        {
            "instruction": "Create a network security group 'nsg-web' in 'network-rg' with an inbound rule allowing TCP 80 from any source.",
            "output": (
                "$rule = New-AzNetworkSecurityRuleConfig -Name 'Allow-HTTP' -Description 'Allow inbound HTTP' "
                "-Access Allow -Protocol Tcp -Direction Inbound -Priority 100 -SourceAddressPrefix * "
                "-SourcePortRange * -DestinationAddressPrefix * -DestinationPortRange 80\n"
                "New-AzNetworkSecurityGroup -Name 'nsg-web' -ResourceGroupName 'network-rg' -Location 'eastus' -SecurityRules $rule"
            ),
        },
        {
            "instruction": "Create a public IP 'pip-web-01' and a NIC 'nic-web-01' attached to VNet 'vnet-hub' subnet 'snet-apps' in 'network-rg' (eastus).",
            "output": (
                "$pip = New-AzPublicIpAddress -Name 'pip-web-01' -ResourceGroupName 'network-rg' -Location 'eastus' "
                "-AllocationMethod Static -Sku Standard\n"
                "$vnet = Get-AzVirtualNetwork -Name 'vnet-hub' -ResourceGroupName 'network-rg'\n"
                "$subnet = Get-AzVirtualNetworkSubnetConfig -Name 'snet-apps' -VirtualNetwork $vnet\n"
                "New-AzNetworkInterface -Name 'nic-web-01' -ResourceGroupName 'network-rg' -Location 'eastus' "
                "-SubnetId $subnet.Id -PublicIpAddressId $pip.Id"
            ),
        },
        {
            "instruction": "List all stopped or deallocated VMs in the current subscription.",
            "output": (
                "Get-AzVM -Status | Where-Object { $_.PowerState -match 'stopped|deallocated' }"
            ),
        },
        {
            "instruction": "Create a Key Vault named 'kv-prod-001' in resource group 'prod-rg' located in 'eastus'.",
            "output": (
                "New-AzKeyVault -Name 'kv-prod-001' -ResourceGroupName 'prod-rg' -Location 'eastus' -Sku Standard"
            ),
        },
        {
            "instruction": "Set a secret named 'DbPassword' with value 'P@ssw0rd!123' in Key Vault 'kv-prod-001'.",
            "output": (
                "Set-AzKeyVaultSecret -VaultName 'kv-prod-001' -Name 'DbPassword' "
                "-SecretValue (ConvertTo-SecureString 'P@ssw0rd!123' -AsPlainText -Force)"
            ),
        },
        {
            "instruction": "List all managed disks that are not attached to any VM.",
            "output": "Get-AzDisk | Where-Object { -not $_.ManagedBy }",
        },
        {
            "instruction": "Create a snapshot named 'osdisk-snap-01' from the managed disk 'osdisk-01' in 'prod-rg' (eastus).",
            "output": (
                "$disk = Get-AzDisk -ResourceGroupName 'prod-rg' -DiskName 'osdisk-01'\n"
                "$cfg = New-AzSnapshotConfig -SourceUri $disk.Id -Location 'eastus' -CreateOption Copy\n"
                "New-AzSnapshot -ResourceGroupName 'prod-rg' -SnapshotName 'osdisk-snap-01' -Snapshot $cfg"
            ),
        },
        {
            "instruction": "Find the public IP addresses of all VMs in resource group 'prod-rg'.",
            "output": (
                "Get-AzPublicIpAddress -ResourceGroupName 'prod-rg' | Where-Object { $_.IpConfiguration -ne $null } "
                "| Select-Object Name, IpAddress"
            ),
        },
        {
            "instruction": "Create a Linux VM named 'web-01' in 'prod-rg' (eastus) of size 'Standard_B2s' using an existing NIC 'nic-web-01'.",
            "output": (
                "New-AzVM -ResourceGroupName 'prod-rg' -Location 'eastus' -Name 'web-01' -Size 'Standard_B2s' "
                "-NetworkInterfaceNames 'nic-web-01' -Image 'Canonical:0001-com-ubuntu-server-jammy:22_04-lts:latest' "
                "-GenerateSshKey"
            ),
        },
        {
            "instruction": "Enable boot diagnostics for VM 'web-01' in 'prod-rg' using storage account 'stdiagprod'.",
            "output": (
                "$vm = Get-AzVM -Name 'web-01' -ResourceGroupName 'prod-rg'\n"
                "Set-AzVMBootDiagnostics -VM $vm -Enable -ResourceGroupName 'prod-rg' -StorageAccountName 'stdiagprod'\n"
                "Update-AzVM -ResourceGroupName 'prod-rg' -VM $vm"
            ),
        },
    ]

    # Additional large set of synthetic tasks (programmatically generated)
    def _add(instruction: str, output: str) -> None:
        pairs.append({"instruction": instruction, "output": output})

    # Resource groups across multiple regions
    _locations = [
        "eastus", "eastus2", "westus", "westus2", "centralus",
        "uksouth", "northeurope", "westeurope", "southeastasia", "australiaeast",
    ]
    for idx, loc in enumerate(_locations, start=1):
        rg = f"ops-rg-{idx}"
        _add(f"Create a resource group '{rg}' in '{loc}'.", f"New-AzResourceGroup -Name '{rg}' -Location '{loc}'")
        _add(f"Delete the resource group '{rg}'.", f"Remove-AzResourceGroup -Name '{rg}' -Force")
        _add(f"List resources in the '{rg}' resource group.", f"Get-AzResource -ResourceGroupName '{rg}'")
        _add(
            f"Tag all resources in '{rg}' with env=dev.",
            "Get-AzResource -ResourceGroupName '{rg}' | ForEach-Object { Update-AzTag -ResourceId $_.ResourceId -Operation Merge -Tag @{ env = 'dev' } }".replace("{rg}", rg),
        )

    # Virtual Machines management (create/start/stop/restart/resize/attach disk/boot diag)
    _vm_sizes = ["Standard_B2s", "Standard_D2s_v5", "Standard_D4s_v5"]
    for i in range(1, 21):
        rg = f"app-rg-{i}"
        vm = f"app-vm-{i:02d}"
        size = _vm_sizes[i % len(_vm_sizes)]
        _add(
            f"Create a Linux VM '{vm}' in '{rg}' (eastus) with size '{size}'.",
            f"New-AzVM -ResourceGroupName '{rg}' -Location 'eastus' -Name '{vm}' -Size '{size}' -Image 'Canonical:0001-com-ubuntu-server-jammy:22_04-lts:latest' -GenerateSshKey",
        )
        _add(f"Start the VM '{vm}' in '{rg}'.", f"Start-AzVM -Name '{vm}' -ResourceGroupName '{rg}'")
        _add(f"Stop and deallocate the VM '{vm}' in '{rg}'.", f"Stop-AzVM -Name '{vm}' -ResourceGroupName '{rg}' -Force")
        _add(f"Restart the VM '{vm}' in '{rg}'.", f"Restart-AzVM -Name '{vm}' -ResourceGroupName '{rg}'")
        _add(
            f"Resize the VM '{vm}' in '{rg}' to '{size}'.",
            f"$vm = Get-AzVM -Name '{vm}' -ResourceGroupName '{rg}'\n$vm.HardwareProfile.VmSize = '{size}'\nUpdate-AzVM -ResourceGroupName '{rg}' -VM $vm",
        )
        _add(
            f"Attach a 128GB data disk to VM '{vm}' in '{rg}'.",
            f"$vm = Get-AzVM -Name '{vm}' -ResourceGroupName '{rg}'\nAdd-AzVMDataDisk -VM $vm -Name '{vm}-data1' -Lun 1 -CreateOption Empty -DiskSizeInGB 128\nUpdate-AzVM -ResourceGroupName '{rg}' -VM $vm",
        )
        _add(
            f"Enable boot diagnostics on VM '{vm}' in '{rg}' using 'stdiag{i:03d}'.",
            f"$vm = Get-AzVM -Name '{vm}' -ResourceGroupName '{rg}'\nSet-AzVMBootDiagnostics -VM $vm -Enable -ResourceGroupName '{rg}' -StorageAccountName 'stdiag{i:03d}'\nUpdate-AzVM -ResourceGroupName '{rg}' -VM $vm",
        )

    # Storage accounts and containers
    for i, loc in enumerate(["eastus2", "westus2", "westeurope", "southeastasia", "uksouth", "northeurope"], start=1):
        rg = f"storage-rg-{i}"
        st = f"stappdata{i:03d}"
        _add(
            f"Create a StorageV2 account '{st}' in '{loc}' with Standard_LRS in '{rg}'.",
            f"New-AzStorageAccount -ResourceGroupName '{rg}' -Name '{st}' -Location '{loc}' -SkuName 'Standard_LRS' -Kind 'StorageV2'",
        )
        _add(f"List keys for storage account '{st}' in '{rg}'.", f"Get-AzStorageAccountKey -ResourceGroupName '{rg}' -Name '{st}'")
        _add(
            f"Create a private blob container 'logs' on '{st}' in '{rg}'.",
            f"$ctx = (Get-AzStorageAccount -ResourceGroupName '{rg}' -Name '{st}').Context\nNew-AzStorageContainer -Name 'logs' -Context $ctx -Permission Off",
        )
        _add(
            f"Upload './web.log' to 'logs' on '{st}' in '{rg}'.",
            f"$ctx = (Get-AzStorageAccount -ResourceGroupName '{rg}' -Name '{st}').Context\nSet-AzStorageBlobContent -File './web.log' -Container 'logs' -Blob 'web.log' -Context $ctx",
        )
        _add(
            f"Enable blob soft delete (7 days) on '{st}'.",
            f"Enable-AzStorageBlobDeleteRetentionPolicy -ResourceGroupName '{rg}' -AccountName '{st}' -RetentionDays 7",
        )

    # Networking: VNet, Subnets, NSG, Public IP, NIC
    for i, loc in enumerate(["eastus", "westeurope", "centralus", "westus2"], start=1):
        rg = f"net-rg-{i}"
        vnet = f"vnet-hub-{i}"
        subnet = f"snet-apps-{i}"
        nsg = f"nsg-web-{i}"
        _add(
            f"Create VNet '{vnet}' with subnet '{subnet}' in '{rg}' at '{loc}'.",
            f"$s = New-AzVirtualNetworkSubnetConfig -Name '{subnet}' -AddressPrefix '10.{i}.1.0/24'\nNew-AzVirtualNetwork -Name '{vnet}' -ResourceGroupName '{rg}' -Location '{loc}' -AddressPrefix '10.{i}.0.0/16' -Subnet $s",
        )
        _add(
            f"Create NSG '{nsg}' with inbound TCP 80 allow in '{rg}'.",
            "$r = New-AzNetworkSecurityRuleConfig -Name 'Allow-HTTP' -Access Allow -Protocol Tcp -Direction Inbound -Priority 100 -SourceAddressPrefix * -SourcePortRange * -DestinationAddressPrefix * -DestinationPortRange 80\nNew-AzNetworkSecurityGroup -Name '{nsg}' -ResourceGroupName '{rg}' -Location '{loc}' -SecurityRules $r".replace("{nsg}", nsg).replace("{rg}", rg).replace("{loc}", loc),
        )
        _add(
            f"Create a static public IP 'pip-web-{i:02d}' in '{rg}' at '{loc}'.",
            f"New-AzPublicIpAddress -Name 'pip-web-{i:02d}' -ResourceGroupName '{rg}' -Location '{loc}' -AllocationMethod Static -Sku Standard",
        )
        _add(
            f"Create NIC 'nic-web-{i:02d}' in '{rg}' attached to '{vnet}/{subnet}'.",
            f"$v = Get-AzVirtualNetwork -Name '{vnet}' -ResourceGroupName '{rg}'\n$sn = Get-AzVirtualNetworkSubnetConfig -Name '{subnet}' -VirtualNetwork $v\nNew-AzNetworkInterface -Name 'nic-web-{i:02d}' -ResourceGroupName '{rg}' -Location '{loc}' -SubnetId $sn.Id",
        )
        _add(
            f"Peer VNets '{vnet}' and 'vnet-spoke-{i}'.",
            f"Add-AzVirtualNetworkPeering -Name '{vnet}-to-spoke' -VirtualNetwork (Get-AzVirtualNetwork -Name '{vnet}' -ResourceGroupName '{rg}') -RemoteVirtualNetworkId (Get-AzVirtualNetwork -Name 'vnet-spoke-{i}' -ResourceGroupName '{rg}').Id -AllowForwardedTraffic -AllowGatewayTransit",
        )

    # Load Balancer (basic example)
    for i in range(1, 6):
        rg = f"lb-rg-{i}"
        _add(
            f"Create a basic public Load Balancer 'lb-web-{i}' in '{rg}' at eastus.",
            "New-AzLoadBalancer -ResourceGroupName '{rg}' -Name 'lb-web-{i}' -Location 'eastus' -Sku Basic -FrontendIpConfiguration @(@{ Name = 'fe'; PublicIpAddress = New-AzPublicIpAddress -Name 'pip-lb-{i}' -ResourceGroupName '{rg}' -Location 'eastus' -AllocationMethod Static }) -BackendAddressPool @(@{ Name = 'bep' }) -Probe @(@{ Name = 'hp'; Protocol = Tcp; Port = 80 }) -LoadBalancingRule @(@{ Name = 'lbr'; Protocol = Tcp; FrontendPort = 80; BackendPort = 80; IdleTimeoutInMinutes = 4; EnableFloatingIP = $false; BackendAddressPool = 'bep'; Probe = 'hp'; FrontendIpConfiguration = 'fe' })".replace("{rg}", rg).replace("{i}", str(i)),
        )

    # Key Vault
    for i, loc in enumerate(["eastus", "westus2", "westeurope", "centralus"], start=1):
        rg = f"sec-rg-{i}"
        kv = f"kv-{i:03d}-prod"
        _add(f"Create a Key Vault '{kv}' in '{rg}' at '{loc}'.", f"New-AzKeyVault -Name '{kv}' -ResourceGroupName '{rg}' -Location '{loc}' -Sku Standard")
        _add("Set a secret 'DbPassword' in '{kv}'.".replace("{kv}", kv), "Set-AzKeyVaultSecret -VaultName '{kv}' -Name 'DbPassword' -SecretValue (ConvertTo-SecureString 'P@ssw0rd!123' -AsPlainText -Force)".replace("{kv}", kv))
        _add(
            f"Grant secret get permissions on '{kv}' to 'alice@contoso.com'.",
            f"Set-AzKeyVaultAccessPolicy -VaultName '{kv}' -UserPrincipalName 'alice@contoso.com' -PermissionsToSecrets get,list",
        )

    # Disks and snapshots
    for i in range(1, 8):
        rg = f"disk-rg-{i}"
        disk = f"osdisk-{i:02d}"
        snap = f"snap-os-{i:02d}"
        _add(f"List unattached managed disks in '{rg}'.", f"Get-AzDisk -ResourceGroupName '{rg}' | Where-Object {{ -not $_.ManagedBy }}")
        _add(
            f"Create a snapshot '{snap}' from disk '{disk}' in '{rg}' (eastus).",
            f"$d = Get-AzDisk -ResourceGroupName '{rg}' -DiskName '{disk}'\n$c = New-AzSnapshotConfig -SourceUri $d.Id -Location 'eastus' -CreateOption Copy\nNew-AzSnapshot -ResourceGroupName '{rg}' -SnapshotName '{snap}' -Snapshot $c",
        )

    # Role assignments
    for role in ["Reader", "Contributor", "Storage Blob Data Reader"]:
        for i in range(1, 3):
            rg = f"auth-rg-{i}"
            _add(
                f"Assign the '{role}' role on '{rg}' to user 'alice@contoso.com'.",
                f"New-AzRoleAssignment -SignInName 'alice@contoso.com' -RoleDefinitionName '{role}' -ResourceGroupName '{rg}'",
            )
            _add(
                f"Remove the '{role}' role on '{rg}' from user 'alice@contoso.com'.",
                f"Remove-AzRoleAssignment -SignInName 'alice@contoso.com' -RoleDefinitionName '{role}' -ResourceGroupName '{rg}'",
            )

    # Azure AD basics
    for i in range(1, 6):
        upn = f"user{i}@contoso.com"
        grp = f"SecGroup{i}"
        _add(
            f"Create Azure AD user '{upn}' requiring password change on first login.",
            f"New-AzureADUser -DisplayName 'User {i}' -UserPrincipalName '{upn}' -AccountEnabled $true -MailNickname 'user{i}' -PasswordProfile @{{ ForceChangePasswordNextLogin = $true; Password = 'Pass@w0rd!' }}",
        )
        _add(f"Create Azure AD group '{grp}'.", f"New-AzureADGroup -DisplayName '{grp}' -MailEnabled $false -MailNickname 'secgroup{i}' -SecurityEnabled $true")
        _add(
            f"Add '{upn}' to group '{grp}'.",
            f"Add-AzureADGroupMember -ObjectId (Get-AzureADGroup -SearchString '{grp}').ObjectId -RefObjectId (Get-AzureADUser -ObjectId '{upn}').ObjectId",
        )

    # Azure SQL
    for i in range(1, 4):
        rg = f"sql-rg-{i}"
        server = f"sqlsvr{i:03d}"
        db = f"sqldb{i:03d}"
        _add(
            f"Create Azure SQL server '{server}' in '{rg}' (eastus).",
            f"New-AzSqlServer -ResourceGroupName '{rg}' -ServerName '{server}' -Location 'eastus' -SqlAdministratorCredentials (Get-Credential)",
        )
        _add(
            f"Create Azure SQL database '{db}' on server '{server}' in '{rg}'.",
            f"New-AzSqlDatabase -ResourceGroupName '{rg}' -ServerName '{server}' -DatabaseName '{db}' -Edition GeneralPurpose -ComputeModel Serverless -ComputeGeneration Gen5 -MinVcores 1 -MaxVcores 4",
        )
        _add(
            f"Add firewall rule to allow Azure services on '{server}'.",
            f"New-AzSqlServerFirewallRule -ResourceGroupName '{rg}' -ServerName '{server}' -AllowAllAzureIPs",
        )

    # Cosmos DB
    for i in range(1, 4):
        rg = f"cosmos-rg-{i}"
        acct = f"cosmos{i:03d}acct"
        _add(
            f"Create Cosmos DB account '{acct}' (SQL API) in '{rg}' at eastus.",
            f"New-AzCosmosDBAccount -ResourceGroupName '{rg}' -Name '{acct}' -Location 'eastus' -DefaultConsistencyLevel Session -ApiKind 'Sql' -EnableAutomaticFailover",
        )
        _add(
            f"Create Cosmos DB database 'appdb' in account '{acct}'.",
            f"New-AzCosmosDBSqlDatabase -ResourceGroupName '{rg}' -AccountName '{acct}' -Name 'appdb'",
        )
        _add(
            f"Create Cosmos DB container 'items' (pk='/id') in '{acct}/appdb'.",
            f"New-AzCosmosDBSqlContainer -ResourceGroupName '{rg}' -AccountName '{acct}' -DatabaseName 'appdb' -Name 'items' -PartitionKeyPath '/id' -Throughput 400",
        )

    # AKS
    for i in range(1, 4):
        rg = f"aks-rg-{i}"
        aks = f"aks-cluster-{i}"
        _add(f"Create AKS cluster '{aks}' in '{rg}' (eastus) with 1 node.", f"New-AzAks -ResourceGroupName '{rg}' -Name '{aks}' -NodeCount 1 -NodeVmSize 'Standard_B4ms' -Location 'eastus'")
        _add(f"Get kubeconfig for AKS '{aks}'.", f"Get-AzAksCredential -ResourceGroupName '{rg}' -Name '{aks}' -Admin")
        _add(f"Scale AKS '{aks}' node count to 2.", f"Update-AzAks -ResourceGroupName '{rg}' -Name '{aks}' -NodeCount 2")

    # ACR
    for i in range(1, 4):
        rg = f"acr-rg-{i}"
        acr = f"acr{i:03d}registry"
        _add(f"Create Azure Container Registry '{acr}' in '{rg}' at eastus.", f"New-AzContainerRegistry -ResourceGroupName '{rg}' -Name '{acr}' -Location 'eastus' -Sku Standard -AdminUserEnabled")
        _add(f"Import image 'nginx:latest' into '{acr}'.", f"Import-AzContainerRegistryImage -ResourceGroupName '{rg}' -RegistryName '{acr}' -SourceImage 'docker.io/library/nginx:latest' -Mode Force")

    # Monitoring
    for i in range(1, 4):
        rg = f"mon-rg-{i}"
        law = f"logws-{i:03d}"
        _add(f"Create Log Analytics workspace '{law}' in '{rg}' at eastus.", f"New-AzOperationalInsightsWorkspace -ResourceGroupName '{rg}' -Location 'eastus' -Name '{law}' -Sku Standard")

    # App Service
    for i in range(1, 5):
        rg = f"appsvc-rg-{i}"
        plan = f"asp-linux-{i}"
        web = f"webapp-{i:03d}"
        _add(f"Create Linux App Service plan '{plan}' (B1) in '{rg}' at eastus.", f"New-AzAppServicePlan -Name '{plan}' -Location 'eastus' -ResourceGroupName '{rg}' -Tier 'Basic' -NumberofWorkers 1 -Linux")
        _add(f"Create Web App '{web}' in '{rg}' on plan '{plan}'.", f"New-AzWebApp -Name '{web}' -ResourceGroupName '{rg}' -Location 'eastus' -AppServicePlan '{plan}'")
        _add(f"Set app setting 'ENV=prod' on '{web}'.", f"Set-AzWebApp -Name '{web}' -ResourceGroupName '{rg}' -AppSettings @{ { 'ENV' : 'prod' } }".replace("@{ {", "@{").replace("} }", "}"))

    # Simple listings to diversify
    _add("List all resource groups.", "Get-AzResourceGroup")
    _add("Show current subscription context.", "Get-AzContext")
    _add("List all subscriptions.", "Get-AzSubscription")
    _add("List VM sizes available in 'eastus'.", "Get-AzVMSize -Location 'eastus'")
    _add("List available locations.", "Get-AzLocation")
    _add("List public IPs in 'net-rg-1'.", "Get-AzPublicIpAddress -ResourceGroupName 'net-rg-1'")
    _add("List network security groups in 'net-rg-1'.", "Get-AzNetworkSecurityGroup -ResourceGroupName 'net-rg-1'")
    _add("List VNets in 'net-rg-1'.", "Get-AzVirtualNetwork -ResourceGroupName 'net-rg-1'")
    _add("List NICs in 'net-rg-1'.", "Get-AzNetworkInterface -ResourceGroupName 'net-rg-1'")
    _add("List Key Vaults in 'sec-rg-1'.", "Get-AzKeyVault -ResourceGroupName 'sec-rg-1'")
    _add("Get Key Vault secret 'DbPassword' from 'kv-001-prod'.", "(Get-AzKeyVaultSecret -VaultName 'kv-001-prod' -Name 'DbPassword').SecretValueText")
    _add("List container registries in subscription.", "Get-AzContainerRegistry")
    _add("List AKS clusters in 'aks-rg-1'.", "Get-AzAks -ResourceGroupName 'aks-rg-1'")
    _add("List Cosmos DB accounts in 'cosmos-rg-1'.", "Get-AzCosmosDBAccount -ResourceGroupName 'cosmos-rg-1'")
    _add("List SQL servers in 'sql-rg-1'.", "Get-AzSqlServer -ResourceGroupName 'sql-rg-1'")

    # Expand with variants to ensure total >= 250
    for i in range(1, 16):
        rg = f"misc-rg-{i}"
        _add(f"Export ARM template for resource group '{rg}'.", f"Export-AzResourceGroup -ResourceGroupName '{rg}' -Path './{rg}-template.json' -IncludeParameterDefaultValue")
        _add(f"Lock resource group '{rg}' with 'CanNotDelete'.", f"New-AzResourceLock -LockName '{rg}-lock' -LockLevel CanNotDelete -ResourceGroupName '{rg}'")
        _add(f"Remove lock '{rg}-lock' from resource group '{rg}'.", f"Remove-AzResourceLock -LockName '{rg}-lock' -ResourceGroupName '{rg}' -Force")

    # Sanity check: ensure we hit the requested scale
    if len(pairs) < 250:
        raise RuntimeError(f"Dataset size too small: {len(pairs)} (<250)")

    return pairs


def write_jsonl(rows: list[dict[str, str]], output_path: Path) -> None:
    """Write the dataset to JSON Lines format, one object per line."""
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            # Minimal validation to ensure required keys exist
            if not {"instruction", "output"}.issubset(row.keys()):
                raise ValueError("Each row must contain 'instruction' and 'output' keys.")
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    dataset_rows = build_azure_powershell_pairs()

    # Write to the repository root, not inside the venv folder
    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / "azure_powershell_dataset.jsonl"
    write_jsonl(dataset_rows, output_path)
    print(f"Wrote {len(dataset_rows)} examples to {output_path}")


if __name__ == "__main__":
    main()




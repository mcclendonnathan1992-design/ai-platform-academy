@description('NSG name.')
param name string

param location string

@description('Source allowed to reach the subnet on 443.')
param allowedSourcePrefix string

resource nsg 'Microsoft.Network/networkSecurityGroups@2024-01-01' = {
  name: name
  location: location
  properties: {
    securityRules: [
      {
        name: 'allow-https-from-hub'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: allowedSourcePrefix
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
      {
        name: 'deny-all-inbound'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

output id string = nsg.id

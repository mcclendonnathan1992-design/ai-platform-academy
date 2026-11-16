param name string
param location string
param addressPrefix string

@description('Array of { name, prefix } objects.')
param subnets array

param nsgId string

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: name
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        addressPrefix
      ]
    }
    subnets: [for s in subnets: {
      name: s.name
      properties: {
        addressPrefix: s.prefix
        networkSecurityGroup: {
          id: nsgId
        }
      }
    }]
  }
}

output id string = vnet.id

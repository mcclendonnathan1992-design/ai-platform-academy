targetScope = 'resourceGroup'

param location string = resourceGroup().location
param environment string = 'dev'
param hubPrefix string = '10.0.0.0/24'
param subnets array = [
  {
    name: 'workload'
    prefix: '10.20.1.0/24'
  }
  {
    name: 'mgmt'
    prefix: '10.20.2.0/24'
  }
]

module nsg 'modules/nsg.bicep' = {
  name: 'nsg-deploy'
  params: {
    name: 'nsg-spoke-${environment}'
    location: location
    allowedSourcePrefix: hubPrefix
  }
}

module vnet 'modules/vnet.bicep' = {
  name: 'vnet-deploy'
  params: {
    name: 'vnet-spoke-${environment}'
    location: location
    addressPrefix: '10.20.0.0/16'
    subnets: subnets
    nsgId: nsg.outputs.id
  }
}

output vnetId string = vnet.outputs.id

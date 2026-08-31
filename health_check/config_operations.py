import sys
config_path='/home/aikernel/src/configs/'
# config_path='/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/src/configs/'
# sys.path.append('../configs/')
sys.path.append(config_path)

import config
MachineID=int(config.MachineID)
locationId=int(config.LocationId)
lane_count=int(config.lane_count)
active_lane=config.active_lane
# print('MachineID : ',MachineID)
# print('locationId : ',locationId)

Logs_Folder_Path='/home/aikernel/health_check_logs/'
# Raw_Json_Folder_Path=config_path+'/raw_jsons/'
# Cron_path='/home/aikernel/src/crons'
# Logs_Folder_Path='/home/linux/DeepLearning/Uday/MP_AVDR/srcs/Algorithm/health_check_logs/'
Json_Folder_Path=config_path+'/jsons/'
Master_Json_Folder_Path='/home/aikernel/metadata/'
Raw_Json_Folder_Path=config_path+'/raw_jsons/'
HealthCheck_Software_Json=Json_Folder_Path+'/healthcheck_software.json'
HealthCheck_Hardware_Json=Json_Folder_Path+'/healthcheck_hardware.json'

# Domain
# Domain='https://mp-dss-api.mahamining.com'
Domain='https://echeckgate.mp.gov.in/dss-api'
Test_Domain='https://mp-dss-test-api.mahamining.com'
#Production_Domain
# Live_Dss_Domain='https://echeckgate.mp.gov.in/dss-api'
# API's
updateSoftwareStatus=Domain+"/MP/HealthCheck/updateSoftwareStatus"
# SaveLaneRestartStatus=Domain+'/MP/Machine/SaveLaneRestartDetails'
SaveMachineRestartDetails=Domain+'/MP/Machine/SaveMachineRestartDetails'
# SaveMachineStorage=Domain+'/mp/Machine/SaveMachineStorage'
# CodeHealthCheckStatus=Domain+'/MP/HealthCheck/running_code_status'

# SaveUpdateLEDLightStatus=Domain+'/MP/HealthCheck/SaveUpdateLEDLightStatus'
# SaveUpdateMicroControllerWorkingStatus=Domain+'/MP/HealthCheck/SaveUpdateMicroControllerWorkingStatus'
# SaveUpdateHeatAnalysis=Domain+'/MP/HealthCheck/SaveUpdateHeatAnalysis'
# SaveUpdatePowerStatusRecord=Domain+'/MP/HealthCheck/SaveUpdatePowerStatusRecord'
# SaveUpdateTamperingStatus=Domain+'/MP/HealthCheck/SaveUpdateTamperingStatus'
# SaveUpdateSoftwareStatus=Domain+'/MP/HealthCheck/SaveUpdateSoftwareStatus'
SaveCameraWorkingStatus=Domain+'/mp/CameraHealthCheck/SaveCameraStatus'
SaveUpdateHardwareStatus=Domain+'/MP/HealthCheck/updateHardwareStatus'

#Config API
# Mahakahnij
GetProfile=Domain+'/MP/monitoring/GetMachineProfileDetailsByMachineIdAndLocationId'
# GetAllMineral='https://awsapi.mahamining.com/mineral-mapping/monitoring/GetAllMineral'
# GetAllColor='https://awsapi.mahamining.com/mineral-mapping/monitoring/GetAllColor' 
# GetAllFrontClassCategory='https://awsapi.mahamining.com/mineral-mapping/monitoring/GetAllFrontClassCategory' 
# GetAllTopClassCategory='https://awsapi.mahamining.com/mineral-mapping/monitoring/GetAllTopClassCategory'
# GetAllSensorMaster='https://mp-dss-api.mahamining.com/MP/Master/GetHardwaredetails'
# 

# #Test
# GetAllMineral='https://mp-dss-test-api.mahamining.com/MP/Master/GetAllMineral'
# GetAllColor='https://mp-dss-test-api.mahamining.com/MP/Master/GetAllColor' 
# GetAllFrontClassCategory='https://mp-dss-test-api.mahamining.com/MP/Master/GetFrontClass' 
# GetAllTopClassCategory='https://mp-dss-test-api.mahamining.com/MP/Master/GetAllTopClassCategory'
# GetAllSensorMaster='https://mp-dss-test-api.mahamining.com/MP/Master/GetHardwaredetails'

#Dev
GetAllMineral=Domain+"/MP/Master/GetAllMineral"
GetAllColor=Domain+"/MP/Master/GetAllColor"
GetAllFrontClassCategory=Domain+"/MP/Master/GetFrontClass"
GetAllTopClassCategory=Domain+"/MP/Master/GetAllTopClassCategory"
GetAllSensorMaster=Domain+'/MP/Master/GetHardwaredetails'


All_Master_API_Dict={
    'get_profile':GetProfile,
    'color_class_category':GetAllColor,
    'mineral_class_category':GetAllMineral,
    'front_class_category':GetAllFrontClassCategory,
    'top_class_category':GetAllTopClassCategory,
    'hardware_class_categroy':GetAllSensorMaster
}

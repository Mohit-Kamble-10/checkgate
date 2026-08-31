import os
import httpx
import json
import datetime
import ssl


# Path to the CA bundle
ca_cert_path = '/home/aikernel/metadata/ca-bundle.pem'

# Create a custom SSL context with legacy renegotiation
def create_custom_ssl_context():
    context = ssl.create_default_context()
    context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT (allows legacy renegotiation)
    context.load_verify_locations(cafile=ca_cert_path)
    return context

def send_images(API=None,base_data=None,files1=None):
    try:
        # Use httpx with the custom SSL context
        # print("base_data : ",base_data)
        timeout = httpx.Timeout(connect=20.0, read=30.0, write=30.0, pool=None)
        with httpx.Client(verify=create_custom_ssl_context(),timeout=15) as client:#, timeout=10
            response_live = client.post(API, data=base_data,files=files1)
        response_live = response_live.json()
        # print("response_live : ",response_live)
        if response_live['statusCode']=="200":
            message='Success'
        else:
            message='Error'
        return response_live,message
    # except httpx.SSLError as e:
    #     print('SSL Error:', e)
    #     return {},"SSL Error: "+str(e)
    except httpx.ConnectError as e:
        print('Connection Error:', e)
        return {},"Connection Error: "+str(e)
    except httpx.RequestError as e:
        print('Request Error:', e)
        return {},"Request Error: "+str(e)
    except ValueError as e:
        print('JSON Decode Error:', e)
        return {},"JSON Decode Error: "+str(e)
    except Exception as e:
        return {},"other error : "+str(e)

def send_json(API=None,json_data=None):
    try:
        # Use httpx with the custom SSL context
        # print("json_data : ",json_data)
        with httpx.Client(verify=create_custom_ssl_context(), timeout=10) as client:
            response_live = client.post(API, json=json_data)
        response_live = response_live.json()
        # print("response_live : ",response_live)
        if response_live['statusCode']=='200':
            message='Success'
        else:
            message='Error'
        return response_live,message
    # except httpx.SSLError as e:
    #     print('SSL Error:', e)
    #     return {},"SSL Error: "+str(e)
    except httpx.ConnectError as e:
        print('Connection Error:', e)
        return {},"Connection Error: "+str(e)
    except httpx.RequestError as e:
        print('Request Error:', e)
        return {},"Request Error: "+str(e)
    except ValueError as e:
        print('JSON Decode Error:', e)
        return {},"JSON Decode Error: "+str(e)
    except Exception as e:
        return {},"other error : "+str(e)

def send_json_get(API=None,params=None):
    try:
        # Use httpx with the custom SSL context
        print("params : ",params)
        with httpx.Client(verify=create_custom_ssl_context(), timeout=10) as client:
            response_live = client.get(API, params=params)
        response_live = response_live.json()
        print("response_live : ",response_live)
        if response_live['statusCode']=='200':
            message='Success'
        else:
            message='Error'
        return response_live,message
    # except httpx.SSLError as e:
    #     print('SSL Error:', e)
    #     return {},"SSL Error: "+str(e)
    except httpx.ConnectError as e:
        print('Connection Error:', e)
        return {},"Connection Error: "+str(e)
    except httpx.RequestError as e:
        print('Request Error:', e)
        return {},"Request Error: "+str(e)
    except ValueError as e:
        print('JSON Decode Error:', e)
        return {},"JSON Decode Error: "+str(e)
    except Exception as e:
        return {},"other error : "+str(e)

import streamlit as st
import json
from datetime import datetime
from glob import glob 

# st.set_page_config(page_title="Models Info", page_icon="🚀", layout="wide")

# Load JSON data
def load_json(path="model_info.json"):
    with open(path, "r") as f:
        data = json.load(f)
        if 'model' in data.keys():
            model_name=data['model'].split("/")[-1]
            data['model_name']=model_name
    return data
# Format datetime string
def format_datetime(dt_string):
    try:
        dt = datetime.strptime(dt_string, "%d_%m_%Y_%H_%M_%S")
        return dt.strftime("%B %d, %Y at %I:%M:%S %p")
    except Exception as e:
        return f"Invalid format: {dt_string}"


def model_loaded_main():
    st.title("📦 Installed Models Info")

    try:
        model_dict={ 
            "ANPR Camera Models" : "",
            "Top Models" : "",
            "Mineral Classification Models" : "",
            "Colour Classification Models" : "",
        }
        model_header='Model'
        json_path_list=glob("/home/aikernel/metadata/loaded_model/**")
        model_data=[]
        for json_path in json_path_list:
            model_data.append(load_json(json_path)) 
        for model in model_data:
            if 'Bonnet' in model['model_name']: model_header ="Colour Classification Model"
            if 'MP_NumberPlate' in model['model_name']: model_header ="ANPR Camera Model"
            if 'MP_Minerla_Classificatio' in model['model_name']: model_header ="Mineral Classification Model"
            if 'Covered_mining' in model['model_name']: model_header ="Top Model"
            
            st.subheader(f"🧠 {model_header}: {model['model_name']}")
            st.write(f"**Model Path:** `{model['model']}`")
            
            formatted_dt = format_datetime(model.get("datetime", ""))
            st.write("Last Run Date & Time: **"+formatted_dt+'**')
            st.markdown("---")
    except Exception as e:
        st.error(f"Failed to load model info: {e}")


# if __name__ == "__main__":
#     model_loaded_main()
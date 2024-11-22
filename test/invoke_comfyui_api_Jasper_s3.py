#!/usr/bin/env python3
import boto3
from botocore.exceptions import NoCredentialsError
from io import BytesIO
import requests
import uuid
import json
import urllib.parse
import sys
import random
import time
import threading
import comfyui_api_utils

# AWS Configuration

S3_BUCKET_NAME = "comfyui-outputs-339712991492-eu-west-2"  # Replace with your S3 bucket name
#S3_FOLDER = "comfyui-images"  # Optional: folder inside the bucket

SERVER_ADDRESS = "http://k8s-default-comfyuii-74cd8f9a9e-1020608794.eu-west-2.elb.amazonaws.com"
SHOW_IMAGES = False


# Initialize S3 client
s3_client = boto3.client('s3')


# Check if the image is ready, if not, upload it
def review_prompt(prompt):
    for node in prompt:
        if 'inputs' in prompt[node] and 'image' in prompt[node]['inputs'] and isinstance(prompt[node]['inputs']['image'], str):
            filename = prompt[node]['inputs']['image']
            if not comfyui_api_utils.check_input_image_ready(filename, SERVER_ADDRESS):
                # image need to be placed at the same dir
                comfyui_api_utils.upload_image(filename, SERVER_ADDRESS)

# Set random seed for the prompt
def random_seed(prompt):
    for node in prompt:
        if 'inputs' in prompt[node]:
            if 'seed' in prompt[node]['inputs']:
                prompt[node]['inputs']['seed'] = random.randint(0, sys.maxsize)
            if 'noise_seed' in prompt[node]['inputs']:
                prompt[node]['inputs']['noise_seed'] = random.randint(0, sys.maxsize)
    return prompt

# Set color for the prompt
def set_color(prompt,colorDetail, colorBody):
    for node in prompt:
        if 'title' in prompt[node]:
            if  prompt[node]['title'] == 'ColorInputDetails' :
                prompt[node]['inputs']['value'] = colorDetail
            if  prompt[node]['title'] == 'ColorInputBody' :
                prompt[node]['inputs']['value'] = colorBody
    return prompt

# Set color for the prompt
def set_Token(prompt,token):
    for node in prompt:
        if 'title' in prompt[node]:
            if  prompt[node]['title'] == 'PromptTokenInput' :
                prompt[node]['inputs']['value'] = token
         
    return prompt

# Set params for the prompt
def set_Params(prompt,colorDetail, colorBody,token):
    for node in prompt:
        if '_meta' in prompt[node]:
            if  prompt[node]['_meta']['title'] == 'ColorInputDetails' :
                prompt[node]['inputs']['value'] = colorDetail
                print("set ColorInputDetails")
            if  prompt[node]['_meta']['title'] == 'ColorInputBody' :
                prompt[node]['inputs']['value'] = colorBody
                print("set ColorInputBody")
            if  prompt[node]['_meta']['title'] == 'PromptTokenInput' :
                prompt[node]['inputs']['value'] = token
                print("set PromptTokenInput")
            if  prompt[node]['_meta']['title'] == 'GlobalSeed' :
                prompt[node]['inputs']['value'] = random.randint(0, sys.maxsize)
                print("set GlobalSeed")
    return prompt

def upload_to_s3(file_name, file_data, bucket_name, s3_key):
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=file_data,
            ContentType='image/png'
        )
        print(f"Uploaded {file_name} to s3://{bucket_name}/{s3_key}")
    except NoCredentialsError:
        print("AWS credentials not found. Ensure they're configured in your environment.")
        raise

def get_images(prompt, client_id, server_address):
    prompt_id, aws_alb_cookie = comfyui_api_utils.queue_prompt(prompt, client_id, server_address)
    output_images = {}

    print("Generation started.")
    while True:
        history = comfyui_api_utils.get_history(prompt_id, server_address, aws_alb_cookie)
        if len(history) == 0:
            print("Generation not ready, sleep 1s ...")
            time.sleep(1)
            continue
        else:
            print("Generation finished.")
            break

    history = history[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output and node_output['images'][0]['type'] == 'output':
            images_output = []
            for image in node_output['images']:
                print(image)
                # image_data = comfyui_api_utils.get_image(image['filename'], image['subfolder'], image['type'], server_address, aws_alb_cookie)
                # images_output.append(image_data)

                # Upload each image to S3
                file_name = image['filename']
                #s3_key = f"{S3_FOLDER}/{file_name}" if S3_FOLDER else file_name
                # s3_key = f"{file_name}"
                # upload_to_s3(file_name, image_data, S3_BUCKET_NAME, s3_key)

            output_images[node_id] = images_output
    return output_images, prompt_id

# Invoke the ComfyUI API with one workflow
def single_inference(server_address, request_api_json):
    start = time.time()
    client_id = str(uuid.uuid4())
    with open(request_api_json, "r") as f:
        prompt = json.load(f)
    review_prompt(prompt)
    prompt = set_Params(prompt,"5005441","12227444","Oarfish")
    images, prompt_id = get_images(prompt, client_id, server_address)
    if SHOW_IMAGES:
        for node_id in images:
            for image_data in images[node_id]:
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(image_data))
                image.show()
    end = time.time()
    timespent = round((end - start), 2)
    print("Inference finished.")
    print(f"ClientID: {client_id}.")
    print(f"PromptID: {prompt_id}.")
    print(f"Num of images: {len(images)}.")
    print(f"Time spent: {timespent}s.")
    print("------")
    
    return images


if __name__ == "__main__":
    # Get the file path from the command line
    if len(sys.argv) == 2:
        REQUEST_API_JSON = sys.argv[1]
    else:
        print("Usage: python3 invoke_comfyui_api.py <request_api_json>")
        sys.exit(1)
    single_inference(SERVER_ADDRESS, REQUEST_API_JSON)

{'filename': '\\21_11\\API_Test\\Regional_Optimized2_JasperColors_LAB\\RegionalPrompt_Optimized2_JasperColors_LABOarfish__00001_.png', 'subfolder': '', 'type': 'output'}
{'filename': '\\21_11\\API_Test\\Regional_Optimized2_JasperColors_LAB\\RegionalPrompt_Optimized2_JasperColors_LABOarfish__Upres_00001_.png', 'subfolder': '', 'type': 'output'}
{'filename': '\\21_11\\API_Test\\Regional_Optimized2_JasperColors_LAB\\RegionalPrompt_Optimized2_JasperColors_LABOarfish_Pallette_00001_.png', 'subfolder': '', 'type': 'output'}
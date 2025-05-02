import time
import requests
from tools import load_prompt
import json

# 配置
server_address = "wp05.unicorn.org.cn:17206"
base_url = f"https://{server_address}"
headers = {'Content-Type': 'application/json'}

# 提交 prompt
prompt_payload = prompt_payload = {"prompt":{
  "6": {
    "inputs": {
      "text": "Scene Location: Mountain Trail Rest Point During Outdoor Team-building.Protagonist Pose:a small cat,cat-agentDemo,cute, Perched on a rocky ledge along the hiking path, forward facing camera directly left hand spreading open a topographic-marked outdoor map, right arm naturally gesturing toward distant sunset Background Description: Hiking backpacks and moisture-proof sit pads scattered along the winding trail, club pennants hanging on cliffside. Foreground rocks hold an open Geology Fundamentals notebook with highlighters, while distant silhouettes show teammates assisting each other on rope nets. Ombré orange-pink sunset dyes layered mountain ranges, cloud gaps reveal glimmering outlines of the campus library above the sea of clouds.",
      "speak_and_recognation":True,
      "clip": [
        "75",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP文本编码器"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "13",
        0
      ],
      "vae": [
        "10",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE解码"
    }
  },
  "10": {
    "inputs": {
      "vae_name": "ae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "VAE加载器"
    }
  },
  "11": {
    "inputs": {
      "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
      "clip_name2": "clip_l.safetensors",
      "type": "flux",
      "device": "default"
    },
    "class_type": "DualCLIPLoader",
    "_meta": {
      "title": "双CLIP加载器"
    }
  },
  "12": {
    "inputs": {
      "unet_name": "flux1-dev-fp8.safetensors",
      "weight_dtype": "fp8_e4m3fn"
    },
    "class_type": "UNETLoader",
    "_meta": {
      "title": "UNET加载器"
    }
  },
  "13": {
    "inputs": {
      "noise": [
        "25",
        0
      ],
      "guider": [
        "22",
        0
      ],
      "sampler": [
        "16",
        0
      ],
      "sigmas": [
        "67",
        0
      ],
      "latent_image": [
        "27",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "自定义采样器(高级)"
    }
  },
  "16": {
    "inputs": {
      "sampler_name": "deis"
    },
    "class_type": "KSamplerSelect",
    "_meta": {
      "title": "K采样器选择"
    }
  },
  "17": {
    "inputs": {
      "scheduler": "beta",
      "steps": 35,
      "denoise": 1,
      "model": [
        "30",
        0
      ]
    },
    "class_type": "BasicScheduler",
    "_meta": {
      "title": "基础调度器"
    }
  },
  "22": {
    "inputs": {
      "model": [
        "30",
        0
      ],
      "conditioning": [
        "26",
        0
      ]
    },
    "class_type": "BasicGuider",
    "_meta": {
      "title": "基础引导"
    }
  },
  "25": {
    "inputs": {
      "noise_seed": 55746797449503
    },
    "class_type": "RandomNoise",
    "_meta": {
      "title": "随机噪波"
    }
  },
  "26": {
    "inputs": {
      "guidance": 3,
      "conditioning": [
        "6",
        0
      ]
    },
    "class_type": "FluxGuidance",
    "_meta": {
      "title": "Flux引导"
    }
  },
  "27": {
    "inputs": {
      "width": 720,
      "height": 720,
      "batch_size": 1
    },
    "class_type": "EmptySD3LatentImage",
    "_meta": {
      "title": "空Latent_SD3"
    }
  },
  "30": {
    "inputs": {
      "max_shift": 1.15,
      "base_shift": 0.5,
      "width": 720,
      "height": 720,
      "model": [
        "75",
        0
      ]
    },
    "class_type": "ModelSamplingFlux",
    "_meta": {
      "title": "模型采样算法Flux"
    }
  },
  "42": {
    "inputs": {
      "text": "",
      "speak_and_recognation":  True,
      "clip": [
        "75",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP文本编码器"
    }
  },
  "64": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "65",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "保存图像"
    }
  },
  "65": {
    "inputs": {
      "samples": [
        "73",
        1
      ],
      "vae": [
        "10",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE解码"
    }
  },
  "66": {
    "inputs": {
      "noise": [
        "71",
        0
      ],
      "guider": [
        "22",
        0
      ],
      "sampler": [
        "16",
        0
      ],
      "sigmas": [
        "67",
        1
      ],
      "latent_image": [
        "68",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "自定义采样器(高级)"
    }
  },
  "67": {
    "inputs": {
      "denoise": 0.45,
      "sigmas": [
        "17",
        0
      ]
    },
    "class_type": "SplitSigmasDenoise",
    "_meta": {
      "title": "分离Sigmas降噪"
    }
  },
  "68": {
    "inputs": {
      "noise_seed": 0,
      "noise_strength": 2.25,
      "normalize": "false",
      "latent": [
        "13",
        0
      ]
    },
    "class_type": "InjectLatentNoise+",
    "_meta": {
      "title": "插入噪波Latent"
    }
  },
  "69": {
    "inputs": {
      "samples": [
        "66",
        1
      ],
      "vae": [
        "10",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE解码"
    }
  },
  "70": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "85",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "保存图像"
    }
  },
  "71": {
    "inputs": {},
    "class_type": "DisableNoise",
    "_meta": {
      "title": "禁用噪波"
    }
  },
  "73": {
    "inputs": {
      "noise": [
        "25",
        0
      ],
      "guider": [
        "22",
        0
      ],
      "sampler": [
        "16",
        0
      ],
      "sigmas": [
        "17",
        0
      ],
      "latent_image": [
        "27",
        0
      ]
    },
    "class_type": "SamplerCustomAdvanced",
    "_meta": {
      "title": "自定义采样器(高级)"
    }
  },
  "75": {
    "inputs": {
      "lora_name": "cat-agentdemo.safetensors",
      "strength_model": 0.9,
      "strength_clip": 0.9,
      "model": [
        "12",
        0
      ],
      "clip": [
        "11",
        0
      ]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "LoRA加载器"
    }
  },
  "79": {
    "inputs": {
      "scale": 0.3,
      "strength": 0.34,
      "saturation": 0.6,
      "toe": 0,
      "seed": 1111622897808073,
      "image": [
        "85",
        0
      ]
    },
    "class_type": "BetterFilmGrain",
    "_meta": {
      "title": "Better Film Grain"
    }
  },
  "80": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "79",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "保存图像"
    }
  },
  "85": {
    "inputs": {
      "upscale_by": 2,
      "seed": 519221671988204,
      "steps": 25,
      "cfg": 1,
      "sampler_name": "deis",
      "scheduler": "beta",
      "denoise": 0.25,
      "mode_type": "Linear",
      "tile_width": 1024,
      "tile_height": 1024,
      "mask_blur": 8,
      "tile_padding": 32,
      "seam_fix_mode": "None",
      "seam_fix_denoise": 1,
      "seam_fix_width": 64,
      "seam_fix_mask_blur": 8,
      "seam_fix_padding": 16,
      "force_uniform_tiles": False,
      "tiled_decode": False,
      "image": [
        "69",
        0
      ],
      "model": [
        "30",
        0
      ],
      "positive": [
        "6",
        0
      ],
      "negative": [
        "42",
        0
      ],
      "vae": [
        "10",
        0
      ],
      "upscale_model": [
        "86",
        0
      ]
    },
    "class_type": "UltimateSDUpscale",
    "_meta": {
      "title": "SD放大"
    }
  },
  "86": {
    "inputs": {
      "model_name": "4x-ClearRealityV1.pth"
    },
    "class_type": "Upscale Model Loader",
    "_meta": {
      "title": "放大模型加载器"
    }
  },
  "88": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "69",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "保存图像"
    }
  }
}}

# Step1: 提交 POST 请求
post_response = requests.post(f"{base_url}/api/prompt", json=prompt_payload, headers=headers, verify=False)
post_response.raise_for_status()
prompt_id = post_response.json().get("prompt_id")
print(f"Prompt ID: {prompt_id}")

# Step2: 轮询 history 状态
history_url = f"{base_url}/history/{prompt_id}"
status_str = ""
max_retries = 1000
for attempt in range(max_retries):
    time.sleep(2)
    history_resp = requests.get(history_url, headers=headers, verify=False)
    history_resp.raise_for_status()
    history_data = history_resp.json().get(prompt_id, {})
    status_info = history_data.get("status", {})
    status_str = status_info.get("status_str", "")
    if status_str == "success":
        print("生成成功！")
        break
    else:
        print(f"第 {attempt + 1} 次检查未完成，状态：{status_str}")
else:
    raise TimeoutError("任务未在规定时间内完成。")

# Step3: 获取图片信息并生成链接
outputs = history_data.get("outputs", {})
image_info = outputs.get("64", {}).get("images", [])
if not image_info:
    raise ValueError("未找到图像输出信息。")

for image in image_info:
    filename = image["filename"]
    subfolder = image["subfolder"]
    folder_type = image["type"]
    final_url = f"http://{server_address}/view?filename={filename}&subfolder={subfolder}&type={folder_type}"
    print("生成图片查看链接：", final_url)
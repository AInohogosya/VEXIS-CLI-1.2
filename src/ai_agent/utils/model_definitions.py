"""
Unified Model Definitions for VEXIS-CLI Ollama Integration
Verified against official Ollama library as of 2025
Single source of truth for all model classifications - WITH ICONS
"""

# Essential model families - drastically reduced for simplicity and performance
MODEL_FAMILIES = {
    "meta": {
        "name": "Meta",
        "description": "Meta's Llama family models - Most popular open source foundation models",
        "icon": "🦙",
        "priority": 1,
        "subfamilies": {
            "llama3.1": {
                "name": "Llama 3.1",
                "description": "Enhanced Llama 3.1 models with 128K context",
                "icon": "🚀",
                "models": {
                    "llama3.1:8b": {"name": "Llama 3.1 8B", "desc": "8B parameters • Enhanced • 128K context", "icon": "⚡"},
                    "llama3.1:70b": {"name": "Llama 3.1 70B", "desc": "70B parameters • Enhanced • 128K context", "icon": "🧠"},
                    "llama3.1:latest": {"name": "Llama 3.1 Latest", "desc": "8B parameters • Enhanced • 128K context", "icon": "⭐"},
                }
            },
            "llama3.2": {
                "name": "Llama 3.2",
                "description": "Lightweight Llama 3.2 models for efficiency",
                "icon": "🕊️",
                "models": {
                    "llama3.2:3b": {"name": "Llama 3.2 3B", "desc": "3B parameters • Lightweight • 128K context", "icon": "🕊️"},
                    "llama3.2:1b": {"name": "Llama 3.2 1B", "desc": "1B parameters • Ultra lightweight • 128K context", "icon": "🪶"},
                    "llama3.2:latest": {"name": "Llama 3.2 Latest", "desc": "3B parameters • Lightweight • 128K context", "icon": "⭐"},
                }
            }
        }
    },
    "google": {
        "name": "Google",
        "description": "Google's Gemma family models - Efficient high-quality open models",
        "icon": "💎",
        "priority": 2,
        "subfamilies": {
            "gemma2": {
                "name": "Gemma 2",
                "description": "Efficient Gemma 2 models",
                "icon": "💎",
                "models": {
                    "gemma2:2b": {"name": "Gemma 2 2B", "desc": "2B parameters • High-performing • Efficient", "icon": "⚡"},
                    "gemma2:9b": {"name": "Gemma 2 9B", "desc": "9B parameters • High-performing • Efficient", "icon": "🧠"},
                    "gemma2:27b": {"name": "Gemma 2 27B", "desc": "27B parameters • High-performing • Efficient", "icon": "💪"},
                }
            },
            "gemma3": {
                "name": "Gemma 3",
                "description": "Latest generation Gemma models with multimodal capabilities",
                "icon": "🔮",
                "models": {
                    "gemma3:latest": {"name": "Gemma 3 Latest", "desc": "4B parameters • 128K context • Multimodal", "icon": "⭐"},
                    "gemma3:12b": {"name": "Gemma 3 12B", "desc": "12B parameters • 128K context • Multimodal", "icon": "💪"},
                    "gemma3:4b": {"name": "Gemma 3 4B", "desc": "4B parameters • 128K context • Multimodal", "icon": "🪶"},
                    "gemma3:1b": {"name": "Gemma 3 1B", "desc": "1B parameters • 32K context • Text only", "icon": "⚡"},
                }
            }
        }
    },
    "deepseek": {
        "name": "DeepSeek",
        "description": "DeepSeek's advanced reasoning models - Exceptional reasoning performance",
        "icon": "🔬",
        "priority": 3,
        "subfamilies": {
            "deepseek-r1": {
                "name": "DeepSeek R1",
                "description": "Advanced reasoning models with exceptional performance",
                "models": {
                    "deepseek-r1:32b": {"name": "DeepSeek R1 32B", "desc": "32B parameters • Reasoning • 128K context", "icon": "💪"},
                    "deepseek-r1:14b": {"name": "DeepSeek R1 14B", "desc": "14B parameters • Reasoning • 128K context", "icon": "🌟"},
                    "deepseek-r1:8b": {"name": "DeepSeek R1 8B", "desc": "8B parameters • Reasoning • 128K context", "icon": "⚡"},
                    "deepseek-r1:latest": {"name": "DeepSeek R1 Latest", "desc": "8B parameters • Reasoning • 128K context", "icon": "⭐"},
                }
            }
        }
    },
    "microsoft": {
        "name": "Microsoft",
        "description": "Microsoft's Phi family models - Efficient Small Language Models",
        "icon": "🔷",
        "priority": 4,
        "subfamilies": {
            "phi3": {
                "name": "Phi-3",
                "description": "Lightweight state-of-the-art open models",
                "icon": "🧠",
                "models": {
                    "phi3:latest": {"name": "Phi-3 Latest", "desc": "3.8B parameters • Lightweight • 128K context", "icon": "⭐"},
                    "phi3:instruct": {"name": "Phi-3 Instruct", "desc": "3.8B parameters • Instruction-tuned • 128K context", "icon": "🧠"},
                    "phi3:mini": {"name": "Phi-3 Mini", "desc": "3.8B parameters • Lightweight • 128K context", "icon": "🪶"},
                    "phi3:medium": {"name": "Phi-3 Medium", "desc": "14B parameters • Strong performance • 128K context", "icon": "💪"},
                }
            },
            "phi4": {
                "name": "Phi-4",
                "description": "Latest generation Phi models with state-of-the-art performance",
                "icon": "🚀",
                "models": {
                    "phi4:14b": {"name": "Phi-4 14B", "desc": "14B parameters • State-of-the-art • 16K context", "icon": "🧠"},
                    "phi4:latest": {"name": "Phi-4 Latest", "desc": "14B parameters • State-of-the-art • 16K context", "icon": "⭐"}
                }
            }
        }
    },
    "mistral": {
        "name": "Mistral",
        "description": "Mistral's high-performance models - European open-source AI leader",
        "icon": "🌪️",
        "priority": 5,
        "subfamilies": {
            "mistral": {
                "name": "Mistral",
                "description": "Popular Mistral 7B models",
                "models": {
                    "mistral": {"name": "Mistral 7B", "desc": "7B parameters • Latest • 32K context", "icon": "⚡"},
                    "mistral:latest": {"name": "Mistral 7B Latest", "desc": "7B parameters • Latest • 32K context", "icon": "⭐"},
                    "mistral:instruct": {"name": "Mistral 7B Instruct", "desc": "7B parameters • Instruction-tuned • 32K context", "icon": "🧠"},
                }
            },
            "mistral-large": {
                "name": "Mistral Large 2",
                "description": "Mistral's flagship Large 2 model with advanced reasoning",
                "models": {
                    "mistral-large": {"name": "Mistral Large 2", "desc": "123B parameters • 128K context • Advanced reasoning", "icon": "👑"},
                    "mistral-large:latest": {"name": "Mistral Large 2 Latest", "desc": "123B parameters • 128K context • Advanced reasoning", "icon": "⭐"},
                }
            }
        }
    },
    "other": {
        "name": "Other Models",
        "description": "Enter custom model name or search Ollama library",
        "icon": "🔧",
        "priority": 6,
        "subfamilies": {
            "custom": {
                "name": "Custom Model",
                "description": "Enter any valid Ollama model name",
                "models": {
                    "custom-input": {"name": "Enter Model Name", "desc": "Type any valid Ollama model name"},
                }
            }
        }
    }
}

# Flatten all models for backward compatibility
PREDEFINED_MODELS = {}
for family_key, family_data in MODEL_FAMILIES.items():
    for subfamily_key, subfamily_data in family_data["subfamilies"].items():
        for model_key, model_data in subfamily_data["models"].items():
            PREDEFINED_MODELS[model_key] = model_data["desc"]

# Helper functions for accessing model data
def get_model_families():
    """Get model families sorted by priority"""
    return dict(sorted(MODEL_FAMILIES.items(), key=lambda x: x[1]["priority"]))

def get_subfamilies(family_key):
    """Get subfamilies for a specific model family"""
    if family_key in MODEL_FAMILIES:
        return MODEL_FAMILIES[family_key]["subfamilies"]
    return None

def get_models_in_subfamily(family_key, subfamily_key):
    """Get models in a specific subfamily"""
    if (family_key in MODEL_FAMILIES and 
        subfamily_key in MODEL_FAMILIES[family_key]["subfamilies"]):
        return MODEL_FAMILIES[family_key]["subfamilies"][subfamily_key]["models"]
    return None

def get_model_hierarchy_path(model_name):
    """Get hierarchy path for a specific model"""
    for family_key, family_data in MODEL_FAMILIES.items():
        for subfamily_key, subfamily_data in family_data["subfamilies"].items():
            if model_name in subfamily_data["models"]:
                return {
                    "family": family_key,
                    "family_name": family_data["name"],
                    "subfamily": subfamily_key,
                    "subfamily_name": subfamily_data["name"],
                    "model": model_name,
                    "description": subfamily_data["models"][model_name]["desc"]
                }
    return None

def get_predefined_models():
    """Get predefined models with descriptions"""
    return PREDEFINED_MODELS.copy()

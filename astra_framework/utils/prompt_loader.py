import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class PromptLoader:
    """Loads and manages prompts from YAML configuration files"""
    
    def __init__(self, prompts_file: Path):
        self.prompts_file = Path(prompts_file)
        self.prompts_data = self._load_prompts()
        
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from YAML file"""
        if not self.prompts_file.exists():
            raise FileNotFoundError(f"Prompts file not found: {self.prompts_file}")
        
        with open(self.prompts_file) as f:
            data = yaml.safe_load(f)
        
        logger.info(f"✅ Loaded prompts from: {self.prompts_file}")
        return data
    
    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """
        Get a prompt by key. If kwargs are provided, it formats the prompt.
        Otherwise, it returns the raw template.
        
        Args:
            prompt_key: Key of the prompt in the YAML file
            **kwargs: Variables to format into the prompt template
            
        Returns:
            Formatted prompt string or raw template
        """
        if prompt_key not in self.prompts_data["prompts"]:
            raise KeyError(f"Prompt '{prompt_key}' not found in {self.prompts_file}")
        
        prompt_config = self.prompts_data["prompts"][prompt_key]
        template = prompt_config["template"]
        
        # If no kwargs, return the raw template
        if not kwargs:
            return template
            
        try:
            formatted = template.format(**kwargs)
            logger.debug(f"📝 Loaded prompt: {prompt_config['name']}")
            return formatted.strip()
        except KeyError as e:
            raise ValueError(
                f"Missing required variable for prompt '{prompt_key}': {e}"
            )
    
    def list_prompts(self) -> Dict[str, str]:
        """List all available prompts"""
        return {
            key: config["description"]
            for key, config in self.prompts_data["prompts"].items()
        }
    
    def get_prompt_metadata(self, prompt_key: str) -> Dict[str, str]:
        """Get metadata for a specific prompt"""
        if prompt_key not in self.prompts_data["prompts"]:
            raise KeyError(f"Prompt '{prompt_key}' not found")
        
        config = self.prompts_data["prompts"][prompt_key]
        return {
            "name": config["name"],
            "description": config["description"]
        }
## `class PromptLoader`

Loads and manages prompts from YAML configuration files

### `def __init__`

### `def _load_prompts`

Load prompts from YAML file

### `def get_prompt`

Get a prompt by key. If kwargs are provided, it formats the prompt.
Otherwise, it returns the raw template.

Args:
    prompt_key: Key of the prompt in the YAML file
    **kwargs: Variables to format into the prompt template
    
Returns:
    Formatted prompt string or raw template

### `def list_prompts`

List all available prompts

### `def get_prompt_metadata`

Get metadata for a specific prompt


"""Practice managing prompts and their versions"""

# imports
from langfuse import get_client

fuse = get_client()

# prompts

prompt1_prod_v1 = fuse.create_prompt(
    name='car-assistant',
    type='text',
    prompt='Answer this question shortly: {{question}}',
    labels=['prod'],
)

prompt1_prod_v2 = fuse.create_prompt(
    name='car-assistant',
    type='text',
    prompt='Answer this question fastly, clearly and SHORTLY: {{question}}',
    labels=['prod'],
)

prompt2_dev_v1 = fuse.create_prompt(
    name='car-assistant',
    type='text',
    prompt='Answer this question detailled: {{question}}',
    labels=['dev'],
)

prompt2_dev_v2 = fuse.create_prompt(
    name='car-assistant',
    type='text',
    prompt='Answer this question clearly and detailled: {{question}}',
    labels=['dev'],
)
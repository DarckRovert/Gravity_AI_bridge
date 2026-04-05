from your_cloud_library import ProviderManager, KeyManager

# Initialize the KeyManager with the necessary credentials
key_manager = KeyManager(api_key='YOUR_API_KEY')

# Create an instance of the ProviderManager with the KeyManager
provider_manager = ProviderManager(key_manager=key_manager)

# Get an instance of the Claude model
claude_model = provider_manager.get_model('Claude')

# Create a prompt to explain recursion in Python
prompt = 'Explain recursion in Python.'

# Call the Claude model to get the explanation
response = claude_model.call(prompt)

# Print the response from Claude
print(response)

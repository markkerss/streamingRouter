import json

def extract_function_names(file_path):
  # Read the JSON file
  with open(file_path, 'r') as f:
    # Read line by line since it's a large file
    functions = set()  # Use a set to store unique function names
    
    for line in f:
      try:
        # Parse each line as JSON
        data = json.loads(line)
        
        # Check if 'function' key exists and contains data
        if 'function' in data and data['function']:
          # Extract function name from each function object
          for func in data['function']:
            if 'name' in func:
              functions.add(func['name'])
          
      except json.JSONDecodeError:
          continue  # Skip invalid JSON lines
    
    # Convert set to sorted list
    function_list = sorted(list(functions))
    
    return function_list

# Use the function
if __name__ == "__main__":
    file_path = "data/simple.json"  # Adjust path as needed
    functions = extract_function_names(file_path)
    
    # Print functions with index
    print("Found", len(functions), "unique functions:\n")
    for i, func in enumerate(functions, 1):
        print(f"{i}. {func}")
    
    # Optionally, save to a file
    with open("data/function_names.txt", "w") as f:
        for func in functions:
            f.write(func + "\n")
    
    print("\nFunction names have also been saved to 'function_names.txt'")

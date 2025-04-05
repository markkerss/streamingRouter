import random
from collections import defaultdict
class LoadBalancer:
    def __init__(self):
        # service_name -> array of servers (random selection)
        self.server_arrays = defaultdict(list)
        
        # service_name -> address -> load (updating loads)
        self.server_loads = defaultdict(dict)
        
        # service_name -> total servers
        self.server_counts = defaultdict(int)
        
    def add_server(self, service_name, address, initial_load=0):
        """Add a new server to the load balancer"""
        # Skip if server already exists
        self.server_loads[service_name][address] = initial_load
        self.server_arrays[service_name].append(address)
        self.server_counts[service_name] += 1
        return True
        
    def remove_server(self, service_name, address):
        """Remove a server from the load balancer"""
        swap_index = -1
        for i in range(len(self.server_arrays[service_name])):
            if self.server_arrays[service_name][i] == address:
                swap_index = i
                break
        if swap_index == -1:
            return False
        last_server = self.server_arrays[service_name].pop()
        self.server_arrays[service_name][swap_index] = last_server

        # Remove from index map
        del self.server_loads[service_name][address]
        self.server_counts[service_name] -= 1
        return True
        
    def update_load(self, service_name, address, load):
        """Update the load for a specific server"""
        try:
            self.server_loads[service_name][address] = load
        except KeyError:
            print(f"Server at {address} not found for service {service_name}")
            
    def increment_load(self, service_name, address, amount=1):
        """Increment the load for a server by the given amount"""
        try:
            self.server_loads[service_name][address] += amount
        except KeyError:
            print(f"Server at {address} not found for service {service_name}")
    
    def decrement_load(self, service_name, address, amount=1):
        """Decrement the load for a server by the given amount"""
        self.increment_load(service_name, address, -amount)
            
    def get_server(self, service_name):
        """Select a server using Power of Two Choices algorithm"""
        if self.server_counts[service_name] == 0:
            print(f"No servers available for service {service_name}")
            return None
            
        if self.server_counts[service_name] == 1:
            return self.server_arrays[service_name][0]  # Return the only server's ID
                    
        # Pick two random indices
        idx1 = random.randint(0, self.server_counts[service_name] - 1)
        idx2 = random.randint(0, self.server_counts[service_name] - 1)
        
        # Ensure we have two different servers
        while idx1 == idx2 and self.server_counts[service_name] > 1:
            idx2 = random.randint(0, self.server_counts[service_name] - 1)
            
        # Compare loads and pick server with lower load
        if self.server_loads[service_name][self.server_arrays[service_name][idx1]] <= self.server_loads[service_name][self.server_arrays[service_name][idx2]]:
            chosen_server = self.server_arrays[service_name][idx1]
        else:
            chosen_server = self.server_arrays[service_name][idx2]
            
        
        return chosen_server
    
    def get_server_load(self, service_name, address):
        """Get the current load of a server"""
        try:
            return self.server_loads[service_name][address]
        except KeyError:
            print(f"Server at {address} not found for service {service_name}")
            return None
    
    def print_all_server_loads(self):
        """Get the current load of all servers for all services"""
        for service_name, loads in self.server_loads.items():
            print(f"Service: {service_name}")
            for address, load in loads.items():
                print(f"  {address}: {load}")

# File: cachesimulator.py
# Author(s): Paul Li
# Date: 12/4/2021
# Section: 505
# E-mail(s): pli5297@tamu.edu
# Description: Simulates cache and physical memory

## @package Cache Simulator
#  Documentation for this cache simulator
#
#  Simulates cache and physical memory

import math, random, sys

RAM = [] # Global physical memory
CACHE = [] # Cache
ram_size = 0 # Number of unique memory addresses (M)
cache_size = 0 # Cache size not including valid and tag bits (C)
block_size = 0 # (B)
n_way = 0 # (E)
num_sets = 0 # (S)
tag_bits = 0 # (t)
index_bits = 0 # (s)
block_bits = 0 # (b)
rep_pol = 0
wh_pol = 0
wm_pol = 0
cache_hits = 0
cache_misses = 0
cache_lru_info = [] # Keeps track of which lines in each set were least recently used

## Documentation for init_phys_mem().
#
#  Initializes physical memory (RAM) with values from the given file and "00" to all other values outside of the range.
def init_phys_mem(filename):
    global RAM
    global ram_size

    print("initialize the RAM:") # Stores user input for how much physical memory to initialize
    user_in = input().split()
    ram_start, ram_end = int(user_in[1], 16), int(user_in[2], 16)
    # Initialize physical memory to be all zeroes
    RAM = ["00"] * 256
    ram_size = ram_end - ram_start + 1

    init_values = [line.rstrip() for line in open(filename)] # List of all initial values from "input.txt"
    for i in range(ram_end + 1):
        # Initialize addresses 0x00 - ram_end with values from init_values
        RAM[i] = init_values[i]
    print("RAM successfully initialized!")

## Documentation for config_cache().
#
#  Prompts the user to enter options for configuring the cache such as cache size, block size, etc. Creates the global variable CACHE at the end of the function
#  which is a list storing the values in cache.
def config_cache():
    global RAM, CACHE, ram_size, cache_size, block_size, n_way, num_sets, tag_bits, index_bits, block_bits, rep_pol, wh_pol, wm_pol, cache_lru_info

    # Configure the cache
    print("configure the cache:")
    # Configure cache size
    cache_size = int(input("cache size: "))
    while (cache_size < 8 or cache_size > 256):
        print("ERROR: invalid cache size")
        cache_size = int(input("cache size: "))

    # Configure block size
    block_size = int(input("data block size: "))

    # Configure set associativity
    n_way = int(input("associativity: "))
    while (n_way != 1 and n_way != 2 and n_way != 4):
        print("ERROR: invalid associativity")
        n_way = int(input("associativity: "))

    # Configure replacement policy
    rep_pol = int(input("replacement policy: "))
    while (rep_pol != 1 and rep_pol != 2):
        print("ERROR: invalid replacement policy")
        rep_pol = int(input("replacement policy: "))
    
    # Configure write-hit policy
    wh_pol = int(input("write hit policy: "))
    while (wh_pol != 1 and wh_pol != 2):
        print("ERROR: invalid write hit policy")
        wh_pol = int(input("write hit policy: "))

    # Configure write-miss policy
    wm_pol = int(input("write miss policy: "))
    while (wm_pol != 1 and wm_pol != 2):
        print("ERROR: invalid write miss policy")
        wm_pol = int(input("write miss policy: "))
    
    num_sets = int(cache_size / (n_way * block_size))
    m = int(math.log(ram_size, 2))
    index_bits = int(math.log(num_sets, 2))
    block_bits = int(math.log(block_size, 2))
    tag_bits = int(m - (index_bits + block_bits))
    index_bits = int(math.log(num_sets, 2))

    cache_lru_info = [[0] * n_way for _ in range(num_sets)]
    CACHE = [[["0", "0", "00"] + ["00"] * block_size] * n_way for _ in range(num_sets)] # Initialize cold cache

    print("cache successfully configured!")

## Documentation for memory_view().
#
#  Displays all the contents in physical memory (RAM) in the terminal.
def memory_view():
    global RAM

    print(f"memory_size: {ram_size}")
    print("memory_content:")
    print("address:data")
    for i in range(0, len(RAM), block_size):
        print(f"{hex(i)}:", end = "")
        for j in range(block_size):
            print(f"{RAM[i+j]}", end= " ")
        print("")

## Documentation for find_ram().
#
#  Finds the block of data in the RAM containing the address and returns the whole block.
#  @param address address of the value we are trying to find in RAM in hexadecimal form
def find_ram(address):
    index = (int(address, 16) // block_size) * block_size # Starting index of block in RAM list
    return RAM[index:index + block_size] # Returns whole block of data

## Documentation for write_to_ram(address, byte).
#
#  Writes the value 'byte' into address's memory in RAM
#  @param address value of the address we are trying to write to in RAM in hexadecimal form
#  @param byte value we are trying to write into RAM
def write_to_ram(address, byte):
    global RAM
    RAM[int(address, 16)] = byte

## Documentation for write_block_to_ram(address, block).
#
#  Writes an entire block to RAM
#  @param address value of an address in the block we are trying to write to in RAM in hexadecimal form
#  @param block block of values we are trying to write into RAM
def write_block_to_ram(address, block):
    global RAM
    start = (int(address, 16) // block_size) * block_size
    RAM[start:start + block_size] = block

## Documentation for convert_to_bin(address).
#
#  Takes a hexadecimal address and returns a dictionary containing the tag, set index, and block offset bits converted into binary from the hexadecimal address.
#  @param address value of an address in hexadecimal form
#  @return original address value in binary form
def convert_to_bin(address):
    address = int(address, 16) # Convert address to decimal first
    address = f"{address:08b}" # Convert address to binary number in form of a string
    tag = address[0:tag_bits] # Tag bits
    index = address[tag_bits:tag_bits + index_bits] # Set index bits
    if (index == ""):
        # When there is one set
        index = "0"
    offset = address[tag_bits + index_bits:] # Block offset bits
    return {"tag":tag, "index":index, "offset":offset}

## Documentation for update_LRU(binary_address, most_recent).
#
#  Helper function for updatin LRU status.
#  @param binary_address value of an address in binary form
#  @param most_recent index of the most recent line that was modified
def update_LRU(binary_address, most_recent):
    global cache_lru_info
    set_index = int(binary_address['index'], 2) # Set index in decimal format

    for i in range(len(CACHE[set_index])):
        if i != most_recent:
            cache_lru_info[set_index][i] += 1
    cache_lru_info[set_index][most_recent] = 0

## Documentation for find_cache(binary_address).
#
#  Takes the binary form of the hexadecimal address and looks for the matching tag bit in cache
#  @param binary_address value of an address in binary form
#  @return The index of the matching block in the set in cache or an empty list meaning not found
def find_cache(binary_address):
    set_index = int(binary_address['index'], 2) # Set index in decimal format
    tag = f"{int(binary_address['tag'], 2):02x}" # Tag in hex format

    # Algorithm for finding the matching block in cache
    for block in CACHE[set_index]:
        if block[0] != "0":
            if block[2] == tag:
                return CACHE[set_index].index(block) # Returns the index of the matching block in cache
    return -1

## Documentation for add_cache(binary_address, block).
#
#  Adds a block of data into cache based on what the tag and set index bits are. Returns the eviction line as well
#  @param binary_address value of an address in binary form
#  @return The index of the evicted line if applicable
def add_cache(binary_address, block):
    global CACHE, cache_lru_info

    set_index = int(binary_address['index'],2)
    tag = f"{int(binary_address['tag'],2):02x}" # Tag in hex format
    added = False

    for i in range(len(CACHE[set_index])):
        if CACHE[set_index][i][0] == "0":
            # Condition for an empty row in cache
            CACHE[set_index][i] = ["1", "0", tag] + block
            added = True
            if (rep_pol == 2):
                # Update LRU status if needed
                update_LRU(binary_address, i)
            return i

    if not added:
        # Condition for full set in cache
        if (rep_pol == 1):
            # Condition for random replacement in miss
            line = random.randint(0, n_way - 1) # Randomly chooses one of the lines in the set to replace

            hex_address = hex(int(bin(int(CACHE[set_index][line][2], 16))[2:] + binary_address['index'], 2))
            dirty_bit = CACHE[set_index][line][1]
            if (dirty_bit == "1"):
                # Condition for handling write-back
                write_block_to_ram(hex_address, CACHE[set_index][line][3:])

            CACHE[set_index][line] = ["1", "0", tag] + block
            return line
        elif (rep_pol == 2):
            # Condition for least recently used policy in miss
            # Gets the least recently used line's index
            least_recent = max(cache_lru_info[set_index])
            lr_index = cache_lru_info[set_index].index(least_recent)

            binary_form = bin(int(CACHE[set_index][lr_index][2], 16))[2:] + binary_address['index'] + binary_address['offset']
            hex_address = hex(int(binary_form, 2))
            dirty_bit = CACHE[set_index][lr_index][1]
            if (dirty_bit == "1"):
                # Condition for handling write-back
                write_block_to_ram(hex_address, CACHE[set_index][lr_index][3:])

            CACHE[set_index][lr_index] = ["1", "0", tag] + block
            
            # Update LRU status
            update_LRU(binary_address, lr_index)
            return lr_index
    
## Documentation for write_to_cache(binary_address, byte, hit).
#
#  Helper function for cache_write() that only modifies cache.
#  @param binary_address value of an address in binary form
#  @param byte new value to write into cache
#  @param hit boolean value that lets the function know if it was a cache-hit/miss in the context of calling this function
def write_to_cache(binary_address, byte, hit):
    global CACHE, cache_lru_info

    set_index = int(binary_address['index'],2)
    tag = f"{int(binary_address['tag'],2):02x}" # Tag in hex format
    offset = int(binary_address['offset'],2) # Offset in decimal format
    line = find_cache(binary_address) # Line index in set of which block to modify
    
    if hit:
        # Condition for writing when hit
        data_block = CACHE[set_index][line] # Data block from cache with address that needs to be modified
        data_block[3 + offset] = byte # Overwrites the data in cache
        data_block[1] = "1" # Set dirty bit to 1

        if (rep_pol == 2):
            # Condition for LRU
            update_LRU(binary_address, line)
    else:
        # Condition for writing when not hit
        data_block = CACHE[set_index][line] # Data block from cache with address that needs to be modified
        data_block[3 + offset] = byte # Overwrites the data in cache
        data_block[1] = "1" # Set dirty bit to 1
        # IMPORTANT DONT DOUBLE UPDATE LRU HERE WHEN NOT HIT B/C IT ALREADY UPDATED WHEN WE ADDED/LOADED THE BLOCK INTO CACHE

## Documentation for cache_read(address).
#
#  Takes an address and tries to read it from cache. Displays the information about the read from cache including hit/miss, set index, tag bits, 
#  and the data at the desired location in cache.
#  @param address value of an address in hexadecimal form
def cache_read(address):
    global RAM, CACHE, cache_hits, cache_misses, cache_lru_info

    binary_address = convert_to_bin(address)
    offset = int(binary_address['offset'],2) # Block offset in decimal form
    set_index = int(binary_address['index'],2) # Set index in decimal form
    tag = int(binary_address['tag'], 2) # Tag bits in decimal form
    hex_tag = f"{tag:02x}"
    hit = False
    if (find_cache(binary_address) != -1):
        # Condition for cache hit
        hit = True
        cache_hits += 1
        ev_line = -1
        update_LRU(binary_address, find_cache(binary_address))
    else:
        # Condition for cache miss
        ev_line = add_cache(binary_address, find_ram(address))
        cache_misses += 1
    data = CACHE[set_index][find_cache(binary_address)][3 + offset]

    print(f"set:{set_index}")
    print(f"tag:{hex_tag}")
    print(f"hit:{'yes' if hit else 'no'}")
    print(f"eviction line:{-1 if hit else ev_line}")
    print(f"ram_address:{-1 if hit else address}")
    print(f"data:0x{data}")

## Documentation for cache_write(address, byte).
#
#  Writes the new byte value into location "address".
#  @param address value of an address in hexadecimal form
#  @param byte new value to write into cache and or RAM
def cache_write(address, byte):
    global RAM, CACHE, cache_hits, cache_misses

    binary_address = convert_to_bin(address)
    set_index = int(binary_address['index'],2) # Set index in decimal form
    tag = int(binary_address['tag'], 2) # Tag bits in decimal form
    hex_tag = f"{tag:02x}"
    byte = byte[2:] # Gets rid of the 0x
    hit = False
    ev_line = -1
    
    if (find_cache(binary_address) != -1):
        # Condition for cache hit
        hit = True
        cache_hits += 1
        if (wh_pol == 1):
            # Condition for write-through policy
            write_to_cache(binary_address, byte, hit)
            write_to_ram(address, byte)
        elif (wh_pol == 2):
            # Condition for write-back policy
            write_to_cache(binary_address, byte, hit)
    else:
        # Condition for cache miss
        cache_misses += 1
        if (wm_pol == 1):
            # Condition for write-allocate policy
            ev_line = add_cache(binary_address, find_ram(address)) # First add to cache (LRU updated in this step)
            write_to_cache(binary_address, byte, hit) # Then write to cache
            if (wh_pol == 1):
                # Condition for write-through after write-miss
                write_to_ram(address, byte)
        elif (wm_pol == 2):
            # Condition for no write-allocate policy
            write_to_ram(address, byte) # ONLY WRITE TO RAM and does not load block into cache
    print(f"set:{set_index}")
    print(f"tag:{hex_tag}")
    print(f"write_hit:{'yes' if hit else 'no'}")
    print(f"eviction_line:{ev_line}")
    print(f"ram_address:{'-1' if hit else address}")
    print(f"data:0x{byte}")
    print(f"dirty_bit:1")

## Documentation for cache_view().
#
#  Displays the contents of cache in terminal including information about the cache size, block size, associativity, replacement policy,
#  write-hit policy, write-miss policy, number of cache hits, and number of cache misses.
def cache_view():
    print(f"cache_size:{cache_size}")
    print(f"data_block_size:{block_size}")
    print(f"associativity:{n_way}")
    print(f"replacement_policy:{'random_replacement' if (rep_pol == 1) else 'least_recently_used'}")
    print(f"write_hit_policy:{'write_through' if wh_pol == 1 else 'write_back'}")
    print(f"write_miss_policy:{'write_allocate' if wm_pol == 1 else 'no_write_allocate'}")
    print(f"number_of_cache_hits:{cache_hits}")
    print(f"number_of_cache_misses:{cache_misses}")
    print("cache_content:")
    for i in range(num_sets):
        for j in range(n_way):
            print(*CACHE[i][j])

## Documentation for cache_flush().
#
#  Resets the cache
def cache_flush():
    global CACHE, cache_lru_info

    # Writes all cotents in cache to RAM
    for i in range(len(CACHE)):
        # i is set index
        for j in range(len(CACHE[i])):
            # j is line index
            if (CACHE[i][j][1] == "1"):
                # If line was modified in cache
                tag = CACHE[i][j][2]
                bin_tag = bin(int(tag, 16))[2:]
                set_index = i
                bin_set_index = bin(set_index)[2:]
                while (len(bin_set_index) < int(math.log(num_sets, 2))):
                    bin_set_index = "0" + bin_set_index
                offset = "0" * block_bits
                hex_address = hex(int(bin_tag + bin_set_index + offset, 2))
                write_block_to_ram(hex_address, CACHE[i][j][3:])

    cache_lru_info = [[0] * n_way for _ in range(num_sets)]
    CACHE = [[["0", "0", "00"] + ["00"] * block_size] * n_way for _ in range(num_sets)] # Initialize cold cache
    print("cache_cleared")

## Documentation for cache_dump().
#
#  Outputs the current state of the cache into a file called "cache.txt"
def cache_dump():
    file = open("cache.txt", "w") # Output file
    for i in range(num_sets):
        # i is set index
        for j in range(n_way):
            # j is line index
            for k in range(3, len(CACHE[i][j])):
                file.write(CACHE[i][j][k] + " ")
            file .write("\n")
    file.close()

## Documentation for memory_dump().
#
#  Outputs the current state of RAM into a file called "ram.txt"
def memory_dump():
    file = open("ram.txt", "w") # Output file
    for val in RAM:
        file.write(val + "\n")
    file.close()

## Documentation for user_prompt().
#
#  Function for user interface menu in terminal
def user_prompt():
    print("*** Cache simulator menu ***")
    print("type one command:")
    print("1. cache-read")
    print("2. cache-write")
    print("3. cache-flush")
    print("4. cache-view")
    print("5. memory-view")
    print("6. cache-dump")
    print("7. memory-dump")
    print("8. quit")
    print("****************************")
    user_in = input().split()
    while (user_in[0] != "quit"):
        if (user_in[0] == "cache-read"):
            cache_read(user_in[1])
        elif (user_in[0] == "cache-write"):
            cache_write(user_in[1], user_in[2])
        elif (user_in[0] == "cache-flush"):
            cache_flush()
        elif (user_in[0] == "cache-view"):
            cache_view()
        elif (user_in[0] == "memory-view"):
            memory_view()
        elif (user_in[0] == "cache-dump"):
            cache_dump()
        elif (user_in[0] == "memory-dump"):
            memory_dump()
        print("*** Cache simulator menu ***")
        print("type one command:")
        print("1. cache-read")
        print("2. cache-write")
        print("3. cache-flush")
        print("4. cache-view")
        print("5. memory-view")
        print("6. cache-dump")
        print("7. memory-dump")
        print("8. quit")
        print("****************************")
        user_in = input().split()
        
## Documentation for main().
#
#  Main function
def main():
    # Initialize the physical memory
    print("*** Welcome to the cache simulator ***")
    init_phys_mem(sys.argv[1])
    config_cache()
    user_prompt()

if __name__ == "__main__":
    main()
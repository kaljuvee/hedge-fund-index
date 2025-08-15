#!/usr/bin/env python3
"""
Script to split the large INFOTABLE.tsv file into smaller chunks for GitHub
"""
import os
import sys

def split_infotable(input_file, output_dir, num_chunks=4):
    """Split INFOTABLE.tsv into smaller chunks"""
    
    print(f"Splitting {input_file} into {num_chunks} chunks...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Count total lines
    with open(input_file, 'r', encoding='utf-8') as f:
        total_lines = sum(1 for _ in f)
    
    print(f"Total lines: {total_lines:,}")
    
    # Calculate lines per chunk (excluding header)
    data_lines = total_lines - 1  # Subtract header
    lines_per_chunk = data_lines // num_chunks
    
    print(f"Lines per chunk: {lines_per_chunk:,}")
    
    # Read header
    with open(input_file, 'r', encoding='utf-8') as f:
        header = f.readline()
    
    # Split the file
    with open(input_file, 'r', encoding='utf-8') as f:
        f.readline()  # Skip header in input
        
        for chunk_num in range(num_chunks):
            chunk_file = os.path.join(output_dir, f'INFOTABLE_chunk_{chunk_num + 1}.tsv')
            
            with open(chunk_file, 'w', encoding='utf-8') as chunk_f:
                # Write header to each chunk
                chunk_f.write(header)
                
                # Determine lines to write for this chunk
                if chunk_num == num_chunks - 1:
                    # Last chunk gets remaining lines
                    lines_to_write = data_lines - (chunk_num * lines_per_chunk)
                else:
                    lines_to_write = lines_per_chunk
                
                # Write data lines
                for i in range(lines_to_write):
                    line = f.readline()
                    if not line:  # End of file
                        break
                    chunk_f.write(line)
            
            # Check file size
            size_mb = os.path.getsize(chunk_file) / (1024 * 1024)
            print(f"Created {chunk_file} - {size_mb:.1f} MB")
    
    print("Splitting complete!")

def main():
    """Main function"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, 'data')
    
    input_file = os.path.join(data_dir, 'INFOTABLE.tsv')
    output_dir = os.path.join(data_dir, 'chunks')
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        sys.exit(1)
    
    split_infotable(input_file, output_dir)

if __name__ == "__main__":
    main()


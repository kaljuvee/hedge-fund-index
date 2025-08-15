#!/usr/bin/env python3
"""
Script to reassemble INFOTABLE.tsv from chunks
"""
import os
import sys
import glob

def reassemble_infotable(chunks_dir, output_file):
    """Reassemble INFOTABLE.tsv from chunks"""
    
    print(f"Reassembling chunks from {chunks_dir} into {output_file}...")
    
    # Find all chunk files
    chunk_pattern = os.path.join(chunks_dir, 'INFOTABLE_chunk_*.tsv')
    chunk_files = sorted(glob.glob(chunk_pattern))
    
    if not chunk_files:
        print(f"Error: No chunk files found in {chunks_dir}")
        sys.exit(1)
    
    print(f"Found {len(chunk_files)} chunk files:")
    for chunk_file in chunk_files:
        size_mb = os.path.getsize(chunk_file) / (1024 * 1024)
        print(f"  {os.path.basename(chunk_file)} - {size_mb:.1f} MB")
    
    # Reassemble the file
    with open(output_file, 'w', encoding='utf-8') as output_f:
        header_written = False
        
        for i, chunk_file in enumerate(chunk_files):
            print(f"Processing {os.path.basename(chunk_file)}...")
            
            with open(chunk_file, 'r', encoding='utf-8') as chunk_f:
                # Handle header
                header = chunk_f.readline()
                if not header_written:
                    output_f.write(header)
                    header_written = True
                
                # Copy data lines
                line_count = 0
                for line in chunk_f:
                    output_f.write(line)
                    line_count += 1
                
                print(f"  Copied {line_count:,} data lines")
    
    # Check final file size
    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\nReassembly complete! Final file: {size_mb:.1f} MB")

def main():
    """Main function"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, 'data')
    
    chunks_dir = os.path.join(data_dir, 'chunks')
    output_file = os.path.join(data_dir, 'INFOTABLE.tsv')
    
    if not os.path.exists(chunks_dir):
        print(f"Error: Chunks directory {chunks_dir} not found!")
        print("Run split_data.py first to create chunks.")
        sys.exit(1)
    
    reassemble_infotable(chunks_dir, output_file)

if __name__ == "__main__":
    main()


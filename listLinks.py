def remove_duplicate_links(input_file, output_file=None):
    """
    Reads a text file with one link per line and removes duplicates.
    Optionally writes the unique links to an output file.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        links = f.read().splitlines()
    
    unique_links = sorted(set(links))  # remove duplicates and sort

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            for link in unique_links:
                f.write(link + '\n')
    
    return unique_links


if __name__ == "__main__":
    input_path = "Untitled-2.txt"
    output_path = "unique_links.txt"
    
    unique = remove_duplicate_links(input_path, output_path)
    print(f"Removed duplicates. {len(unique)} unique links saved to {output_path}.")

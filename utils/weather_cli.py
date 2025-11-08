#!/usr/bin/env python3
"""
Weather CLI - A command-line tool to fetch and display weather information
using the wttr.in service.
"""

import sys
import argparse
import requests

API_BASE_URL = "https://wttr.in"

def parse_arguments():
    """
    Parse command line arguments for the Weather CLI.
    
    Returns:
        argparse.Namespace: Parsed arguments containing city and format attributes
    """
    parser = argparse.ArgumentParser(
        description='Fetch and display current weather information for any city',
        prog='weather_cli',
        epilog='Example: python weather_cli.py Paris --format detailed'
    )
    
    parser.add_argument(
        'city',
        type=str,
        help='Name of the city to get weather information for'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['simple', 'detailed'],
        default='simple',
        help='Display format: "simple" for compact one-line output, "detailed" for full ASCII art report (default: simple)'
    )
    
    return parser.parse_args()

def fetch_weather(city, format_type='simple'):
    """
    Fetch weather data from wttr.in service.
    
    Args:
        city (str): Name of the city to get weather for
        format_type (str): Display format ('simple' or 'detailed')
    
    Returns:
        str: Weather data as formatted text from wttr.in
    
    Raises:
        requests.exceptions.HTTPError: For API errors (404, etc.)
        requests.exceptions.ConnectionError: For network issues
        requests.exceptions.Timeout: For timeout issues
    """
    if format_type == 'simple':
        url = f"{API_BASE_URL}/{city}?format=3&T"
    else:
        url = f"{API_BASE_URL}/{city}?T"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            print(f"❌ Error: City '{city}' not found. Please check the spelling.")
            sys.exit(1)
        
        if response.status_code != 200:
            print(f"❌ Error: Unable to fetch weather data. Status code: {response.status_code}")
            sys.exit(1)
        
        return response.text
        
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out. Please try again.")
        sys.exit(1)
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Unable to connect to weather service. Check your internet connection.")
        sys.exit(1)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: An unexpected error occurred: {e}")
        sys.exit(1)

def display_weather(weather_data, format_type='simple'):
    """
    Display formatted weather information to the console.
    
    Args:
        weather_data (str): Weather data from wttr.in
        format_type (str): Display format ('simple' or 'detailed')
    """
    lines_to_remove = [
        'Follow @igor_chubin for wttr.in updates',
        'Follow @igor_chubin'
    ]
    
    filtered_lines = []
    for line in weather_data.split('\n'):
        if not any(promo in line for promo in lines_to_remove):
            filtered_lines.append(line)
    
    weather_data = '\n'.join(filtered_lines)
    
    try:
        if format_type == 'simple':
            print(weather_data.strip())
        else:
            print(weather_data)
    except UnicodeEncodeError:
        print(weather_data.encode('utf-8', errors='replace').decode('utf-8'))

def main():
    """
    Main execution flow for the Weather CLI.
    Orchestrates argument parsing, weather data fetching, and display.
    
    Exit codes:
        0: Success
        1: Error occurred (handled by fetch_weather)
    """
    try:
        args = parse_arguments()
        
        weather_data = fetch_weather(args.city, args.format)
        
        display_weather(weather_data, args.format)
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error: An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

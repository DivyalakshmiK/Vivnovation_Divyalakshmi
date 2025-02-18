import os
import pandas as pd
import folium
from ipywidgets import interact, widgets, Layout, HBox, VBox, HTML, Output
from IPython.display import display, clear_output
import urllib.request
import urllib.parse
import json
import time
from math import radians, cos, sin, asin, sqrt

# Geocoding function using Census API
def geocode_address_census(address):
    """
    Geocode a single address using Census Geocoding API with basic urllib
    """
    try:
        encoded_address = urllib.parse.quote(address)
        base_url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        url = f"{base_url}?address={encoded_address}&benchmark=Public_AR_Current&format=json"
        
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            
        if data['result']['addressMatches']:
            match = data['result']['addressMatches'][0]
            return {
                'latitude': match['coordinates']['y'],
                'longitude': match['coordinates']['x'],
                'status': 'matched'
            }
        return {'latitude': None, 'longitude': None, 'status': 'no_match'}
            
    except Exception as e:
        return {'latitude': None, 'longitude': None, 'status': 'error'}

# Helper function to calculate Haversine distance
def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

# Function to find nearest providers
def find_nearest_providers(user_address, providers_df, num_results=5):
    """
    Find the nearest healthcare providers based on user's address
    
    Parameters:
    user_address (str): The user's address to geocode
    providers_df (DataFrame): DataFrame with provider data
    num_results (int): Number of nearest providers to return
    
    Returns:
    pd.DataFrame: DataFrame with the nearest providers
    """
    # Step 1: Geocode the user's address
    user_location = geocode_address_census(user_address)
    
    # Check if geocoding was successful
    if user_location['status'] != 'matched':
        return pd.DataFrame(), "Could not geocode the address. Please try again with a more specific address."
    
    user_lat = user_location['latitude']
    user_lon = user_location['longitude']
    
    # Step 2: Calculate distance for each provider
    distances = []
    for index, row in providers_df.iterrows():
        # Skip providers without coordinates
        if pd.isna(row['latitude']) or pd.isna(row['longitude']):
            continue
        
        # Calculate distance
        distance = haversine_distance(
            user_lat, user_lon,
            row['latitude'], row['longitude']
        )
        
        # Store provider info with distance
        distances.append({
            'NPI': row['NPI'],
            'Name': row['Name'],
            'Type': row['Type'],
            'Description': row['Description'],
            'has_phone': row['has_phone'],
            'Address': row['Address'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'Distance_km': round(distance, 2)
        })
    
    # Step 3: Convert to DataFrame and sort by distance
    if distances:
        results_df = pd.DataFrame(distances)
        results_df = results_df.sort_values('Distance_km').head(num_results)
        return results_df, None
    else:
        return pd.DataFrame(), "No providers with valid coordinates found"

# Function to list all Excel files in the directory
def list_excel_files(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.xlsx')]
    cleaned_names = {f: f.rsplit('_geocoded', 1)[0].rsplit('_async', 1)[0] for f in files}  # Clean file names
    return cleaned_names

# Function to load data from the selected Excel file
def load_data(file_path):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip()
    df_cleaned = pd.DataFrame({
        'NPI': df['NPI Number'].astype(str),
        'Name': df['Name'].fillna('Unknown'),
        'Type': df['Type'],
        'Description': df['Description'],
        'has_phone': df['Office Verified Number'].notna(),
        'Address': df['Address'],
        'latitude': df['latitude'],
        'longitude': df['longitude']
    })
    return df_cleaned

# Main application function
def run_enhanced_provider_map_app(directory="./geocoded"):
    # Create UI elements and layout
    title = HTML(
        value="<h1 style='text-align:center;'>Healthcare Provider Map & Nearest Provider Lookup</h1>",
        layout=Layout(width='100%')
    )
    
    # Get list of all Excel files and clean names
    files_dict = list_excel_files(directory)
    
    # Create tabs for different features
    tab = widgets.Tab()
    tab_map = VBox()
    tab_nearest = VBox()
    tab.children = [tab_map, tab_nearest]
    tab.set_title(0, 'Provider Map')
    tab.set_title(1, 'Find Nearest Providers')
    
    #################################################
    # MAP TAB COMPONENTS
    #################################################
    
    # Create widgets with horizontal layout
    file_dropdown = widgets.Dropdown(
        options=[(clean_name, file_name) for file_name, clean_name in files_dict.items()],
        description='<b>File:</b>',
        style={'description_width': '50px'},
        layout=Layout(width='220px')
    )
    
    provider_dropdown = widgets.Dropdown(
        description='<b>Provider:</b>',
        disabled=True,
        style={'description_width': '70px'},
        layout=Layout(width='240px')
    )
    
    np_type_dropdown = widgets.Dropdown(
        description='<b>NP Type:</b>',
        disabled=True,
        style={'description_width': '70px'},
        layout=Layout(width='240px')
    )
    
    phone_checkbox = widgets.Checkbox(
        value=False,
        description='With phone only',
        disabled=True,
        indent=False,
        layout=Layout(width='140px')
    )
    
    count_display = HTML(
        value="<p style='margin:0; padding-top:8px'><b>Providers:</b> 0 shown</p>",
        layout=Layout(width='150px')
    )
    
    # Create buttons
    apply_button = widgets.Button(
        description='Apply Filters',
        disabled=True,
        button_style='primary',
        layout=Layout(width='120px')
    )
    
    reset_button = widgets.Button(
        description='Reset',
        disabled=True,
        button_style='warning',
        layout=Layout(width='80px')
    )
    
    # Create output area for the map
    map_output = Output(
        layout=Layout(
            width='97%',
            height='700px',
            border='1px solid #ddd',
            padding='10px',
            margin='10px 0'
        )
    )
    
    #################################################
    # NEAREST PROVIDERS TAB COMPONENTS
    #################################################
    
    nearest_file_dropdown = widgets.Dropdown(
        options=[(clean_name, file_name) for file_name, clean_name in files_dict.items()],
        description='<b>File:</b>',
        style={'description_width': '50px'},
        layout=Layout(width='220px')
    )
    
    address_input = widgets.Text(
        value='',
        placeholder='Enter your address (e.g. 123 Main St, San Juan, PR 00901)',
        description='<b>Address:</b>',
        disabled=True,
        style={'description_width': '70px'},
        layout=Layout(width='500px')
    )
    
    num_results_dropdown = widgets.Dropdown(
        options=[('3 results', 3), ('5 results', 5), ('10 results', 10)],
        value=5,
        description='<b>Show:</b>',
        disabled=True,
        style={'description_width': '70px'},
        layout=Layout(width='150px')
    )
    
    find_button = widgets.Button(
        description='Find Nearest Providers',
        disabled=True,
        button_style='primary',
        layout=Layout(width='180px')
    )
    
    nearest_output = Output(
        layout=Layout(
            width='97%',
            height='500px',
            border='1px solid #ddd',
            padding='10px',
            margin='10px 0'
        )
    )
    
    map_nearest_output = Output(
        layout=Layout(
            width='97%',
            height='400px',
            border='1px solid #ddd',
            padding='10px',
            margin='10px 0'
        )
    )
    
    # Current data and map state
    current_state = {'df': None, 'last_map': None, 'nearest_df': None}
    
    #################################################
    # MAP TAB FUNCTIONS
    #################################################
    
    # Update map based on filters
    def update_map():
        with map_output:
            clear_output(wait=True)
            filtered_df = current_state['df'].copy()
            selected_type = provider_dropdown.value
            np_type = np_type_dropdown.value
            phone_only = phone_checkbox.value
            
            if selected_type != 'All':
                filtered_df = filtered_df[filtered_df['Description'] == selected_type]
            if np_type != 'All':
                filtered_df = filtered_df[filtered_df['Type'] == np_type]
            if phone_only:
                filtered_df = filtered_df[filtered_df['has_phone']]
            
            m = folium.Map(location=[18.2208, -66.5901], zoom_start=9)
            
            # Add markers
            for _, row in filtered_df.iterrows():
                popup_text = f"""
                <b>{'Name: ' + str(row['Name']) if row['Name'] != 'Unknown' else 'NPI: ' + str(row['NPI'])}</b><br>
                Type: {str(row['Description'])}<br>
                NP Type: {str(row['Type'])}<br>
                {'📞 Has phone number' if row['has_phone'] else ''}<br>
                Address: {str(row['Address'])}
                """
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=popup_text,
                    icon=folium.Icon(color='blue')
                ).add_to(m)
            
            # Update count display
            count_display.value = f"<p style='margin:0; padding-top:8px'><b>Providers:</b> {len(filtered_df)} of {len(current_state['df'])} shown</p>"
            
            # Display the map
            display(m)
            current_state['last_map'] = m
    
    # Handle file selection for map
    def on_file_selected(change):
        if change['new']:
            file_path = os.path.join(directory, change['new'])
            df = load_data(file_path)
            current_state['df'] = df
            
            # Update dropdowns
            provider_types = ['All'] + sorted(list(df['Description'].dropna().unique()))
            np_types = ['All'] + sorted(list(df['Type'].dropna().unique()))
            
            provider_dropdown.options = provider_types
            provider_dropdown.value = 'All'
            np_type_dropdown.options = np_types
            np_type_dropdown.value = 'All'
            
            # Enable all controls
            provider_dropdown.disabled = False
            np_type_dropdown.disabled = False
            phone_checkbox.disabled = False
            apply_button.disabled = False
            reset_button.disabled = False
            
            # Update map
            update_map()
    
    # Apply filters button click
    def on_apply_clicked(b):
        update_map()
    
    # Reset filters button click
    def on_reset_clicked(b):
        provider_dropdown.value = 'All'
        np_type_dropdown.value = 'All'
        phone_checkbox.value = False
        update_map()
    
    #################################################
    # NEAREST PROVIDERS TAB FUNCTIONS
    #################################################
    
    # Handle file selection for nearest providers
    def on_nearest_file_selected(change):
        if change['new']:
            file_path = os.path.join(directory, change['new'])
            df = load_data(file_path)
            current_state['nearest_df'] = df
            
            # Enable controls
            address_input.disabled = False
            num_results_dropdown.disabled = False
            find_button.disabled = False
            
            with nearest_output:
                clear_output(wait=True)
                print("File loaded successfully. Enter your address to find nearest providers.")
            
            with map_nearest_output:
                clear_output(wait=True)
    
    # Find nearest providers
    def on_find_clicked(b):
        with nearest_output:
            clear_output(wait=True)
            
            # Validate address
            if not address_input.value.strip():
                print("Please enter an address.")
                return
            
            print(f"Finding nearest providers to {address_input.value}...")
            nearest_df, error_msg = find_nearest_providers(
                address_input.value,
                current_state['nearest_df'],
                num_results_dropdown.value
            )
            
            if error_msg:
                print(f"Error: {error_msg}")
                return
                
            if nearest_df.empty:
                print("No providers found. Please try a different address or dataset.")
                return
            
            # Display results table
            print(f"Found {len(nearest_df)} nearest providers:")
            display(nearest_df[['Name', 'Type', 'Description', 'Address', 'Distance_km']].style.set_properties(**{'text-align': 'left'}))
            
            # Display results on map
            with map_nearest_output:
                clear_output(wait=True)
                
                # Create map centered on user location
                user_loc = geocode_address_census(address_input.value)
                if user_loc['status'] == 'matched':
                    m = folium.Map(location=[user_loc['latitude'], user_loc['longitude']], zoom_start=10)
                    
                    # Add user marker
                    folium.Marker(
                        location=[user_loc['latitude'], user_loc['longitude']],
                        popup="Your location",
                        icon=folium.Icon(color='red', icon='home', prefix='fa')
                    ).add_to(m)
                    
                    # Add provider markers
                    for _, row in nearest_df.iterrows():
                        popup_text = f"""
                        <b>{'Name: ' + str(row['Name']) if row['Name'] != 'Unknown' else 'NPI: ' + str(row['NPI'])}</b><br>
                        Type: {str(row['Description'])}<br>
                        NP Type: {str(row['Type'])}<br>
                        {'📞 Has phone number' if row['has_phone'] else ''}<br>
                        Address: {str(row['Address'])}<br>
                        <b>Distance: {row['Distance_km']} km</b>
                        """
                        folium.Marker(
                            location=[row['latitude'], row['longitude']],
                            popup=popup_text,
                            icon=folium.Icon(color='blue')
                        ).add_to(m)
                    
                    display(m)
    
    

    file_dropdown.observe(on_file_selected, names='value')
    apply_button.on_click(on_apply_clicked)
    reset_button.on_click(on_reset_clicked)
    
    # Register callbacks for nearest providers tab
    nearest_file_dropdown.observe(on_nearest_file_selected, names='value')
    find_button.on_click(on_find_clicked)
    
    # Create horizontal controls layout for map tab
    controls_box = HBox([
        file_dropdown,
        provider_dropdown,
        np_type_dropdown,
        phone_checkbox,
        apply_button,
        reset_button,
        count_display
    ], layout=Layout(
        width='97%',
        padding='10px',
        margin='0 0 5px 0',
        border='1px solid #ddd',
        justify_content='space-between',
        align_items='center'
    ))
    
    nearest_controls_box = HBox([
        nearest_file_dropdown,
        address_input,
        num_results_dropdown,
        find_button
    ], layout=Layout(
        width='97%',
        padding='10px',
        margin='0 0 5px 0',
        border='1px solid #ddd',
        justify_content='flex-start',
        align_items='center'
    ))
    
    tab_map.children = [controls_box, map_output]
    tab_nearest.children = [nearest_controls_box, nearest_output, map_nearest_output]
    
    main_layout = VBox([
        title,
        tab
    ])
    
    display(main_layout)


if __name__ == "__main__":
    run_enhanced_provider_map_app("./geocoded") 

    
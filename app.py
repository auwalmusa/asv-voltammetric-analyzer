import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.signal import find_peaks, savgol_filter

def apply_technique(potential, current, technique, params):
   if technique == 'LSV':
       return process_lsv(potential, current, params)
   elif technique == 'DPV':
       return process_dpv(potential, current, params)
   elif technique == 'SWV':
       return process_swv(potential, current, params)

def process_lsv(potential, current, params):
   scan_rate = params['scan_rate']
   corrected = savgol_filter(current, window_length=21, polyorder=2)
   return corrected

def process_dpv(potential, current, params):
   pulse_amplitude = params['amplitude']
   step_potential = params['step_potential']
   # DPV processing
   forward_current = current[::2]
   backward_current = current[1::2]
   difference_current = forward_current - backward_current
   return difference_current

def process_swv(potential, current, params):
   frequency = params['frequency']
   amplitude = params['amplitude']
   # SWV processing
   forward_current = current[::2]
   backward_current = current[1::2]
   net_current = forward_current - backward_current
   return net_current

def optimize_asv_parameters(data, metal, technique):
   technique_params = {
       'LSV': {'scan_rate': 0.05},
       'DPV': {'amplitude': 0.025, 'step_potential': 0.004},
       'SWV': {'frequency': 25, 'amplitude': 0.025}
   }
   
   processed_current = apply_technique(
       data['Potential'].values,
       data['Current'].values,
       technique,
       technique_params[technique]
   )
   
   return {
       'deposition_potential': -1.2,
       'deposition_time': 120,
       **technique_params[technique]
   }

def create_asv_app():
   st.title("ASV Parameter Optimization")

   technique = st.selectbox("Select Technique", ['LSV', 'DPV', 'SWV'])
   
   with st.sidebar:
       st.header(f"ASV Parameters ({technique})")
       common_params = {
           'deposition_potential': st.slider("Deposition Potential (V)", -1.5, 0.0, -1.2, 0.1),
           'deposition_time': st.slider("Deposition Time (s)", 0, 600, 120, 30)
       }
       
       technique_params = {}
       if technique == 'LSV':
           technique_params['scan_rate'] = st.slider("Scan Rate (V/s)", 0.01, 0.5, 0.05, 0.01)
       elif technique == 'DPV':
           technique_params.update({
               'step_potential': st.slider("Step Potential (V)", 0.001, 0.01, 0.004, 0.001),
               'amplitude': st.slider("Amplitude (V)", 0.01, 0.1, 0.025, 0.005)
           })
       elif technique == 'SWV':
           technique_params.update({
               'frequency': st.slider("Frequency (Hz)", 10, 100, 25, 5),
               'amplitude': st.slider("Amplitude (V)", 0.01, 0.1, 0.025, 0.005)
           })

   metals = ["Pb", "Cd", "Cu", "Hg", "Zn"]
   selected_metals = st.multiselect("Select Metals", metals)
   
   uploaded_file = st.file_uploader(f"Upload {technique} Data (CSV)", type=['csv'])
   
   if uploaded_file and selected_metals:
       try:
           data = pd.read_csv(uploaded_file)
           params = {**common_params, **technique_params}
           
           for metal in selected_metals:
               st.subheader(f"{metal} Analysis ({technique})")
               processed_data = apply_technique(
                   data['Potential'].values,
                   data['Current'].values,
                   technique,
                   params
               )
               
               col1, col2 = st.columns(2)
               with col1:
                   fig = go.Figure()
                   fig.add_trace(go.Scatter(x=data['Potential'], y=data['Current'],
                                          name='Raw Data'))
                   fig.add_trace(go.Scatter(x=data['Potential'][:len(processed_data)], 
                                          y=processed_data,
                                          name=f'{technique} Processed'))
                   fig.update_layout(title=f"{metal} {technique} Voltammogram",
                                   xaxis_title="Potential (V)",
                                   yaxis_title="Current (µA)")
                   st.plotly_chart(fig)
               
               with col2:
                   optimal_params = optimize_asv_parameters(data, metal, technique)
                   st.write("Optimal Parameters:")
                   for param, value in optimal_params.items():
                       st.metric(f"{param.replace('_', ' ').title()}", 
                               f"{value:.3f}" if isinstance(value, float) else value)
               
               st.write("---")
               
       except Exception as e:
           st.error(f"Error processing file: {str(e)}")
           st.error("Please ensure CSV has 'Potential' and 'Current' columns")

if __name__ == "__main__":
   create_asv_app()

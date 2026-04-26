import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Date Corrected Sniper Engine", layout="wide")

st.title("MAYA AI 🎯: Sniper Target Engine (100% Date Corrected)")
st.markdown("Is engine mein **Date Match Logic** poori tarah theek kar diya gaya hai. Ab Histry Match usi din ki prediction aur result ko aapas mein match karega, aur kal ki prediction bilkul alag se nikalega.")

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
selected_end_date = st.sidebar.date_input("Calculation Date (Aaj ki Tarikh)")
max_limit = st.sidebar.slider("Elimination Limit", 2, 5, 4)

shift_order = ["DB", "SG", "FD", "GD", "ZA", "GL", "DS"]

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.sort_values(by='DATE').reset_index(drop=True)
        for col in shift_order:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')

        # Current Data up to selected date
        filtered_df = df[df['DATE'].dt.date <= selected_end_date].copy()
        if len(filtered_df) == 0: st.stop()
        
        target_date_next = selected_end_date + timedelta(days=1)
        st.info(f"📅 **Selected Date (Histry Match):** {selected_end_date.strftime('%d %B %Y')} | 🎯 **Next Prediction:** {target_date_next.strftime('%d %B %Y')}")

        # --- 2. CORE LOGIC ---
        def get_sub_parts(past_list, limit):
            past_list = [int(x) for x in past_list if pd.notna(x)]
            scores = {n: 0 for n in range(100)}
            elim = set()
            for days in range(1, len(past_list) + 1):
                sheet = past_list[-days:]
                counts = Counter(sheet)
                if len(counts) == len(sheet) and len(sheet) > 1: elim.update(sheet)
                for num, freq in counts.items():
                    if freq >= limit: elim.add(num)
                    scores[num] += freq
            ranked = sorted(range(100), key=lambda x: scores[x], reverse=True)
            return {
                "H1": ranked[0:11], "H2": ranked[11:22], "H3": ranked[22:33],
                "M1": ranked[33:44], "M2": ranked[44:55], "M3": ranked[55:66],
                "L1": ranked[66:77], "L2": ranked[77:88], "L3": ranked[88:100],
                "ELIM": list(elim)
            }

        def get_part_name(num, sp_dict):
            for part, nums in sp_dict.items():
                if part != "ELIM" and num in nums: return part
            return None

        def render_ank(nums, jackpots):
            nums = list(set(nums)) 
            nums.sort()
            html = "<div style='display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;'>"
            for n in nums:
                bg = "#2e2e2e"; border = "2px solid #555"; color="white"
                if n in jackpots: bg = "#FF4B4B"; border = "2px solid #ff9999" 
                html += f"<div style='background:{bg}; padding:10px; border-radius:8px; text-align:center; min-width:45px; border:{border}; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);'>" \
                        f"<span style='font-size:22px; font-weight:bold; color:{color};'>{n:02d}</span></div>"
            html += "</div>"
            return html

        # MASTER PREDICTION FUNCTION (Ek hi logic ko alag-alag dates ke liye use karne ke liye)
        def get_sniper_prediction(history_series):
            historical_states = []
            for i in range(15, len(history_series)):
                h_past = history_series[:i]
                sp_past = get_sub_parts(h_past[-15:], max_limit)
                
                loc_strk = 0
                for b in range(1, 10):
                    if i-b < 15: break
                    sp_b = get_sub_parts(history_series[:i-b][-15:], max_limit)
                    b_preds = sp_b['H1'] + sp_b['H2'] + sp_b['H3']
                    if history_series[i-b] not in b_preds: loc_strk += 1
                    else: break
                    
                state = f"L{loc_strk}"
                actual_winner_part = get_part_name(history_series[i], sp_past)
                if actual_winner_part:
                    historical_states.append({"state": state, "winner_part": actual_winner_part})

            # Find STATE at the end of the provided history series
            current_sp = get_sub_parts(history_series[-15:], max_limit)
            cur_loc_strk = 0
            for b in range(1, 10):
                if len(history_series)-b < 15: break
                sp_b = get_sub_parts(history_series[:len(history_series)-b][-15:], max_limit)
                b_preds = sp_b['H1'] + sp_b['H2'] + sp_b['H3']
                if history_series[-b] not in b_preds: cur_loc_strk += 1
                else: break
            
            current_state = f"L{cur_loc_strk}"

            # TARGET SELECTION
            matching_history = [s['winner_part'] for s in historical_states if s['state'] == current_state]
            if matching_history:
                counts = Counter(matching_history)
                top_parts = [x[0] for x in counts.most_common(3)]
            else:
                top_parts = ['H1', 'H2', 'H3']

            all_possible = ['H1', 'H2', 'H3', 'M1', 'M2', 'M3', 'L1', 'L2', 'L3']
            for p in all_possible:
                if len(top_parts) >= 3: break
                if p not in top_parts: top_parts.append(p)

            target_nums = current_sp[top_parts[0]] + current_sp[top_parts[1]] + current_sp[top_parts[2]]
            jackpots = current_sp["ELIM"]

            return target_nums, jackpots, top_parts, current_state

        # --- 3. SHIFT PROCESSING WITH CORRECT DATES ---
        for shift_name in shift_order:
            if shift_name not in df.columns: continue
            
            # Data UP TO Selected Date (For Tomorrow's prediction)
            history_today = filtered_df[shift_name].dropna().astype(int).tolist()
            # Data STRICTLY BEFORE Selected Date (For Histry Match prediction)
            history_yesterday = df[df['DATE'].dt.date < selected_end_date][shift_name].dropna().astype(int).tolist()
            
            if len(history_today) < 30: continue
            
            st.markdown(f"---")
            st.subheader(f"🧩 Shift: {shift_name}")

            with st.spinner("Date match and target lock kiya jaa raha hai..."):
                
                # A. HISTRY MATCH (Correct Logic)
                # Hum 24 tarikh ka data dekar 25 tarikh ke target numbers nikal rahe hain
                actual_row = df[df['DATE'].dt.date == selected_end_date]
                actual_val = int(actual_row.iloc[0][shift_name]) if not actual_row.empty and pd.notna(actual_row.iloc[0][shift_name]) else None
                
                is_hit = False
                if actual_val is not None and len(history_yesterday) >= 30:
                    hist_target_nums, _, _, _ = get_sniper_prediction(history_yesterday)
                    is_hit = actual_val in hist_target_nums

                # B. TOMORROW'S PREDICTION
                # Hum 25 tarikh tak ka data dekar 26 tarikh ke target numbers nikal rahe hain
                final_target_nums, jackpots, top_parts, today_state = get_sniper_prediction(history_today)

            # C. DISPLAY UI
            status_color = "#00FF7F"
            parts_joined = ", ".join(top_parts)
            
            c_res, c_stat = st.columns([1, 2.5])
            with c_res:
                if actual_val is not None:
                    m_color = "#28a745" if is_hit else "#FF4B4B"
                    st.markdown(f"<div style='background:{m_color}; padding:10px; border-radius:8px; text-align:center; color:white;'>"
                                f"Histry Match ({selected_end_date.strftime('%d %b')}):<br><b style='font-size:24px;'>{actual_val:02d}</b><br>{'HIT! ✅' if is_hit else 'MISS ❌'}</div>", unsafe_allow_html=True)
                else:
                    st.write("Histry Match unavailable.")
            
            with c_stat:
                st.markdown(f"<div style='border:2px solid {status_color}; padding:10px; border-radius:8px; background:{status_color}15;'>"
                            f"<b style='color:{status_color}; font-size:18px;'>🎯 SNIPER TARGET LOCKED FOR TOMORROW</b><br>"
                            f"<span style='font-size: 14px;'>Operator State: <b>{today_state}</b> | AI Selected Parts: <b>{parts_joined}</b></span></div>", unsafe_allow_html=True)

            # CLEAR NUMBER DISPLAY
            st.markdown(f"<h4 style='margin-top: 15px;'>Kewal Yehi Numbers Khelne Hain ({target_date_next.strftime('%d %b')} ke liye):</h4>", unsafe_allow_html=True)
            st.markdown(render_ank(final_target_nums, jackpots), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error: {e}")
        

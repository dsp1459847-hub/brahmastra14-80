import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta
from collections import Counter

st.set_page_config(page_title="MAYA AI - Final Sniper Engine", layout="wide")

st.title("MAYA AI 🏆: Final Sniper & Date-Corrected Engine")
st.markdown("Yeh final code hai jisme **History Match Date** aur **Prediction Date** ko 100% sahi kar diya gaya hai.")

# --- 1. Sidebar ---
st.sidebar.header("📁 Data Settings")
uploaded_file = st.sidebar.file_uploader("Upload CSV/Excel", type=['csv', 'xlsx'])
selected_date = st.sidebar.date_input("Calculation Date (Aaj ki tarikh)")
max_limit = st.sidebar.slider("Elimination Limit", 2, 5, 4)

shift_order = ["DB", "SG", "FD", "GD", "ZA", "GL", "DS"]

if uploaded_file is not None:
    try:
        # Load Data
        if uploaded_file.name.endswith('.csv'): df = pd.read_csv(uploaded_file)
        else: df = pd.read_excel(uploaded_file)
        
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        df = df.sort_values(by='DATE').reset_index(drop=True)
        for col in shift_order:
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')

        # Logic Dates
        # Data available UP TO selected_date
        current_data = df[df['DATE'].dt.date <= selected_date].copy()
        if len(current_data) == 0: st.stop()
        
        tomorrow_date = selected_date + timedelta(days=1)
        
        st.success(f"✅ **Data Loaded up to:** {selected_date}")
        st.info(f"🎯 **Prediction For:** {tomorrow_date.strftime('%d %B %Y')} (Tomorrow)")

        # --- 2. CORE LOGIC ENGINE ---
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

        def get_best_adaptive_parts(history_list, state):
            # Markov-style adaptive selection
            historical_winners = []
            for i in range(20, len(history_list)):
                h_past = history_list[:i]
                actual = history_list[i]
                # Check what part won in similar state (Simplified for speed)
                sp = get_sub_parts(h_past[-15:], max_limit)
                for p, nums in sp.items():
                    if p != "ELIM" and actual in nums:
                        historical_winners.append(p)
                        break
            if not historical_winners: return ["H1", "M1", "L1"]
            counts = Counter(historical_winners)
            return [x[0] for x in counts.most_common(3)]

        def render_ank_box(nums, jackpots, votes):
            nums.sort()
            html = "<div style='display: flex; flex-wrap: wrap; gap: 6px;'>"
            for n in nums:
                v = votes.get(n, 0)
                bg = "#FF4B4B" if n in jackpots else "#2e2e2e"
                border = "2px solid #ff9999" if n in jackpots else "1px solid #444"
                html += f"<div style='background:{bg}; border:{border}; padding:6px; border-radius:6px; text-align:center; min-width:40px;'>" \
                        f"<span style='font-size:18px; font-weight:bold; color:white;'>{n:02d}</span><br>" \
                        f"<span style='font-size:9px; color:#aaa;'>{v}v</span></div>"
            html += "</div>"
            return html

        # --- 3. ALL SHIFT PROCESSING ---
        timeframes = [3, 5, 7, 10, 14, 15, 20, 25, 30]
        
        for shift in shift_order:
            if shift not in df.columns: continue
            st.markdown(f"---")
            st.subheader(f"🧩 Shift: {shift}")

            # A. HISTORY MATCH (Correct Date Logic)
            # 1. Prediction for 'Today' was made using data up to 'Yesterday'
            yesterday_data = df[df['DATE'].dt.date < selected_date][shift].dropna().astype(int).tolist()
            actual_today = current_data[current_data['DATE'].dt.date == selected_date][shift].values
            
            is_hit = False
            today_val = int(actual_today[0]) if len(actual_today) > 0 and pd.notna(actual_today[0]) else None
            
            if len(yesterday_data) > 30 and today_val is not None:
                match_votes = []
                for tf in timeframes:
                    if len(yesterday_data) < tf: continue
                    sp_match, _ = get_sub_parts(yesterday_data[-tf:], max_limit)
                    # Adaptive check for yesterday
                    win_parts = get_best_adaptive_parts(yesterday_data, "any")
                    match_votes.extend(sp_match[win_parts[0]] + sp_match[win_parts[1]] + sp_match[win_parts[2]])
                if today_val in match_votes: is_hit = True

            # B. TOMORROW'S PREDICTION (Sniper Mode)
            target_history = current_data[shift].dropna().astype(int).tolist()
            if len(target_history) < 30: 
                st.warning("Insufficient history for this shift.")
                continue
                
            all_votes, jackpot_pool = [], []
            for tf in timeframes:
                if len(target_history) < tf: continue
                # Adaptive selection for tomorrow
                win_parts = get_best_adaptive_parts(target_history, "current")
                today_sp, today_el = get_sub_parts(target_history[-tf:], max_limit)
                preds = today_sp[win_parts[0]] + today_sp[win_parts[1]] + today_sp[win_parts[2]]
                all_votes.extend(preds)
                jackpot_pool.extend([n for n in preds if n in today_el])

            vote_counts = Counter(all_votes)
            final_35 = [x[0] for x in vote_counts.most_common(35)]
            f_jackpots = list(set([n for n in final_35 if n in jackpot_pool]))

            # C. UI DISPLAY
            col_match, col_status = st.columns([1, 2.5])
            with col_match:
                m_color = "#28a745" if is_hit else "#555"
                st.markdown(f"<div style='background:{m_color}; padding:10px; border-radius:8px; text-align:center; color:white;'>"
                            f"Histry Match ({selected_date.strftime('%d %b')}):<br><b style='font-size:20px;'>{today_val if today_val is not None else '--'}</b><br>{'HIT! ✅' if is_hit else 'MISS ❌'}</div>", unsafe_allow_html=True)
            
            with col_status:
                # Streak Logic
                streak = 0
                for i in range(1, 15):
                    if len(target_history) < i+15: break
                    if target_history[-i] not in final_35: streak += 1
                    else: break
                
                status = "NORMAL (1x)"
                s_color = "#1E90FF"
                if streak >= 3: status = "🔥 HIGHLY CONFIRMED (9x)"; s_color = "#00FF7F"
                elif streak == 2: status = "⚡ STRONG (2x)"; s_color = "#FFA500"
                
                st.markdown(f"<div style='border:2px solid {s_color}; padding:10px; border-radius:8px; background:{s_color}15;'>"
                            f"<b style='color:{s_color}; font-size:18px;'>{status}</b><br>"
                            f"Current Loss Streak: {streak} days | Sniper Mode Active</div>", unsafe_allow_html=True)

            st.write(f"**Predictions for Tomorrow ({tomorrow_date.strftime('%d %b')}):**")
            p1, p2, p3 = final_35[0:11], final_35[11:23], final_35[23:35]
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown("🥇 **PART 1**"); st.markdown(render_ank_box(p1, f_jackpots, vote_counts), unsafe_allow_html=True)
            with col2: st.markdown("🥈 **PART 2**"); st.markdown(render_ank_box(p2, f_jackpots, vote_counts), unsafe_allow_html=True)
            with col3: st.markdown("🥉 **PART 3**"); st.markdown(render_ank_box(p3, f_jackpots, vote_counts), unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error logic fix: {e}")
        

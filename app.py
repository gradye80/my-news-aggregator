import streamlit as st
import pandas as pd
from gdeltdoc import GdeltDoc, Filters
from groq import Groq
from datetime import datetime, timedelta

st.set_page_config(page_title="My AI News Aggregator", layout="wide")
st.title("📰 My AI-Powered News Aggregator")
st.caption("Critical Mention style • GDELT + Groq Llama • 100% Free on Cloud")

# Sidebar
st.sidebar.header("Settings")
keywords = st.sidebar.text_input("Keywords / Brand", "Tinker Air Force Base OR Hill Air Force Base OR Warner Robins Air Force Base")
days_back = st.sidebar.slider("Look back (days)", 1, 30, 7)
min_relevance = st.sidebar.slider("Minimum relevance score", 1, 10, 6)
model_choice = st.sidebar.selectbox("Groq Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])

if st.button("🔄 Fetch & Analyze Fresh News", type="primary"):
    with st.spinner("Fetching news + Groq analyzing... (may take 30–90 sec)"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        f = Filters(keyword=keywords, start_date=start_date, end_date=end_date, num_records=80)  # lowered for free-tier safety
        
        gd = GdeltDoc()
        df = gd.article_search(f)
        
        if df.empty:
            st.error("No articles found. Try broader keywords.")
        else:
            results = []
            progress_bar = st.progress(0)
            
            for i, row in df.iterrows():
                progress_bar.progress((i+1)/len(df))
                
                article_text = f"Title: {row['title']}\nURL: {row['url']}\nDate: {row['seendate']}"
                
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": "You are a professional media analyst..."},
                        {"role": "user", "content": f"Keywords: {keywords}\n\nArticle:\n{article_text}"}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                
                ai_text = response.choices[0].message.content
                
                # Simple parsing (same as before)
                relevance = 7
                sentiment = "neutral"
                summary = ai_text[:200]
                alert = "No"
                
                if "relevance" in ai_text.lower():
                    try:
                        relevance = int(''.join(filter(str.isdigit, ai_text.split("relevance")[0][-10:])))
                    except:
                        pass
                if "positive" in ai_text.lower(): sentiment = "positive"
                elif "negative" in ai_text.lower(): sentiment = "negative"
                if "alert" in ai_text.lower() or "high impact" in ai_text.lower():
                    alert = "YES 🔥"
                
                if relevance >= min_relevance:
                    results.append({
                        "Title": row['title'],
                        "URL": row['url'],
                        "Date": row['seendate'],
                        "Domain": row['domain'],
                        "Relevance": relevance,
                        "Sentiment": sentiment,
                        "Alert": alert,
                        "AI Summary": summary
                    })
            
            if results:
                result_df = pd.DataFrame(results).sort_values("Relevance", ascending=False)
                st.success(f"Found {len(result_df)} relevant mentions!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Mentions", len(result_df))
                col2.metric("Alerts", len(result_df[result_df["Alert"] == "YES 🔥"]))
                col3.metric("Avg Relevance", round(result_df["Relevance"].mean(), 1))
                
                st.dataframe(result_df, use_container_width=True, hide_index=True,
                             column_config={"URL": st.column_config.LinkColumn("URL")})
                
                csv = result_df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv, "news_mentions.csv", "text/csv")
            else:
                st.info("No articles above relevance threshold.")

st.info("💡 Tip: Refresh the page or click the button again. Groq is free but has daily limits — don't spam the button.")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Nassau Candy Profitability", layout="wide")

@st.cache_data
def load_data():
    df=pd.read_csv("data/cleaned_nassau_candy.csv")
    df["Order Date"]=pd.to_datetime(df["Order Date"])
    return df

df=load_data()
st.title("Nassau Candy Distributor — Product Line Profitability & Margin Performance")
st.caption("Sales, cost, gross-profit, margin and portfolio diagnostics")

min_date=df["Order Date"].min().date(); max_date=df["Order Date"].max().date()
a,b,c=st.columns(3)
start=a.date_input("Start date",min_date,min_value=min_date,max_value=max_date)
end=b.date_input("End date",max_date,min_value=min_date,max_value=max_date)
division=c.selectbox("Division",["All"]+sorted(df["Division"].unique()))

f=df[(df["Order Date"].dt.date>=start)&(df["Order Date"].dt.date<=end)].copy()
if division!="All": f=f[f["Division"]==division]

threshold=st.slider("Margin-risk threshold (%)",0,100,50)
search=st.text_input("Product search")
if search: f=f[f["Product Name"].str.contains(search,case=False,na=False)]

sales=f.Sales.sum(); profit=f["Gross Profit"].sum(); cost=f.Cost.sum(); units=f.Units.sum()
margin=profit/sales*100 if sales else 0
m1,m2,m3,m4=st.columns(4)
m1.metric("Revenue",f"${sales:,.2f}"); m2.metric("Gross Profit",f"${profit:,.2f}"); m3.metric("Gross Margin",f"{margin:.2f}%"); m4.metric("Units",f"{units:,.0f}")

st.subheader("Product Profitability Leaderboard")
p=f.groupby(["Product ID","Product Name","Division"],as_index=False).agg(Sales=("Sales","sum"),Units=("Units","sum"),Gross_Profit=("Gross Profit","sum"),Cost=("Cost","sum"))
p["Gross Margin (%)"]=p.Gross_Profit/p.Sales*100; p["Profit per Unit"]=p.Gross_Profit/p.Units
p["Profit Contribution (%)"]=p.Gross_Profit/profit*100 if profit else 0
p["Margin Risk"]=np.where(p["Gross Margin (%)"]<threshold,"Review","Healthy")
st.dataframe(p.sort_values("Gross_Profit",ascending=False),use_container_width=True)
st.plotly_chart(px.bar(p.sort_values("Gross_Profit"),x="Gross_Profit",y="Product Name",orientation="h",title="Gross Profit by Product"),use_container_width=True)

st.subheader("Division Performance")
v=f.groupby("Division",as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"),Cost=("Cost","sum"))
v["Gross Margin (%)"]=v.Gross_Profit/v.Sales*100
st.plotly_chart(px.bar(v,x="Division",y=["Sales","Gross_Profit"],barmode="group",title="Revenue vs Gross Profit by Division"),use_container_width=True)
st.dataframe(v,use_container_width=True)

st.subheader("Cost vs Margin Diagnostics")
st.plotly_chart(px.scatter(p,x="Sales",y="Cost",size="Gross_Profit",color="Gross Margin (%)",hover_name="Product Name",title="Product Cost vs Sales"),use_container_width=True)
st.write("Margin-risk products")
st.dataframe(p[p["Gross Margin (%)"]<threshold].sort_values("Gross Margin (%)"),use_container_width=True)

st.subheader("Profit Concentration")
pareto=p.sort_values("Gross_Profit",ascending=False).copy(); pareto["Cumulative Profit (%)"]=pareto.Gross_Profit.cumsum()/profit*100 if profit else 0
st.plotly_chart(px.bar(pareto,x="Product Name",y="Gross_Profit",title="Gross Profit Concentration"),use_container_width=True)
st.dataframe(pareto[["Product Name","Gross_Profit","Cumulative Profit (%)"]],use_container_width=True)

st.subheader("Key Findings")
st.markdown("""- Chocolate is the dominant profit engine.
- Five Wonka Bar products generate about **95.1% of total gross profit**.
- **Kazookles** is the clearest margin-risk product at about **7.69% gross margin**.
- The Other division has materially weaker margin than Chocolate and Sugar.
- Overall monthly gross margin is relatively stable.
- Supplied ship dates extend far beyond order dates and should be validated before logistics conclusions are drawn.
""")

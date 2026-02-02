with r2:
                # --- Existing Pie Chart (Unchanged) ---
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Technical", "Soft Skills"],
                            values=[res["tech"], res["soft"]],
                            hole=0.45,
                            marker=dict(colors=['#60a5fa', '#1d4ed8']) # Match colors with image
                        )
                    ]
                )
                fig.update_layout(
                    height=350, 
                    margin=dict(t=0, b=0, l=0, r=0),
                    showlegend=True,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="white")
                )
                st.plotly_chart(fig, use_container_width=True)

                # --- New Simple Metrics Bar (To fill space) ---
                # Indicator style la irukum, unnecessary lines irukaadhu
                fig_bar = go.Figure(go.Bar(
                    x=[res["tech"], res["soft"]],
                    y=["Technical  ", "Soft Skills  "], # Extra space for padding
                    orientation='h',
                    marker=dict(color=['#60a5fa', '#1d4ed8']),
                    text=[f"Tech: {res['tech']}%", f"Soft: {res['soft']}%"],
                    textposition='inside',
                    insidetextanchor='middle',
                    width=0.6 # Simple and thin
                ))

                fig_bar.update_layout(
                    height=180,
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(visible=False, range=[0, 100]),
                    yaxis=dict(showgrid=False, font=dict(color="white")),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    bargap=0.3
                )
                st.plotly_chart(fig_bar, use_container_width=True)
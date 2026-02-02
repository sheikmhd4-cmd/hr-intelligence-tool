with r2:
                # --- Existing Pie Chart ---
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Technical", "Soft Skills"],
                            values=[res["tech"], res["soft"]],
                            hole=0.45,
                            marker=dict(colors=['#60a5fa', '#1d4ed8']) # Light blue & Deep blue
                        )
                    ]
                )
                fig.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)

                # --- New Simple Bar Chart (To fill empty space) ---
                fig_bar = go.Figure(go.Bar(
                    x=[res["tech"], res["soft"]],
                    y=["Technical", "Soft Skills"],
                    orientation='h',
                    marker=dict(color=['#60a5fa', '#1d4ed8']),
                    text=[f"{res['tech']}%", f"{res['soft']}%"],
                    textposition='auto',
                ))

                fig_bar.update_layout(
                    height=150,
                    margin=dict(t=20, b=20, l=0, r=0),
                    xaxis=dict(visible=False),
                    yaxis=dict(showgrid=False),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False
                )
                st.plotly_chart(fig_bar, use_container_width=True)
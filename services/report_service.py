import io
import csv
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from services.currency_service import CurrencyService

class ReportService:
    @staticmethod
    def generate_pdf_report(analysis_data, regression_data=None, forecast_data=None, output_path=None, currency_code='USD'):
        """
        Generates a publication-grade, professional PDF report of the sales analysis,
        regression model, forecasts, and statistical disclosures with dynamic currency formatting.
        """
        buffer = io.BytesIO() if output_path is None else None
        doc_target = output_path if output_path is not None else buffer
        
        doc = SimpleDocTemplate(
            doc_target,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        # Custom palette & typography
        primary_color = colors.HexColor('#1e40af')
        secondary_color = colors.HexColor('#2563eb')
        dark_text = colors.HexColor('#0f172a')
        muted_text = colors.HexColor('#475569')
        bg_light = colors.HexColor('#f8fafc')
        border_color = colors.HexColor('#cbd5e1')
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=primary_color,
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=muted_text,
            spaceAfter=14
        )
        
        section_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=primary_color,
            spaceBefore=12,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=dark_text
        )
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=muted_text
        )
        
        elements = []
        
        # 1. Header & Title
        title_text = analysis_data.get('title', 'Sales Analysis & Forecasting Report')
        elements.append(Paragraph(title_text, title_style))
        
        generated_date = datetime.now().strftime("%B %d, %Y at %H:%M")
        ds_file = analysis_data.get('dataset_filename', 'Uploaded Dataset')
        row_cnt = analysis_data.get('row_count', 'N/A')
        cur_info = CurrencyService.get_currency(currency_code)
        elements.append(Paragraph(f"Generated on {generated_date} | Source: {ds_file} ({row_cnt} records) | Currency: {cur_info['name']}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=secondary_color, spaceAfter=14))
        
        # 2. Executive Summary KPIs Table
        elements.append(Paragraph(f"1. Executive Summary & Core KPIs ({cur_info['code']})", section_style))
        stats = analysis_data.get('summary_stats', {})
        
        kpi_data = [
            [
                Paragraph("<b>Total Revenue</b>", body_style),
                Paragraph(CurrencyService.format(stats.get('total_revenue', 0), currency_code), body_style),
                Paragraph("<b>Total Units Sold</b>", body_style),
                Paragraph(f"{stats.get('total_units', 0):,}", body_style)
            ],
            [
                Paragraph("<b>Average Sale</b>", body_style),
                Paragraph(CurrencyService.format(stats.get('average_sale', 0), currency_code), body_style),
                Paragraph("<b>Sales Growth Rate</b>", body_style),
                Paragraph(f"{stats.get('sales_growth_rate', 'N/A')}%" if stats.get('sales_growth_rate') is not None else "N/A", body_style)
            ],
            [
                Paragraph("<b>Date Span</b>", body_style),
                Paragraph(str(stats.get('date_range_str', 'N/A')), body_style),
                Paragraph("<b>Median Sale</b>", body_style),
                Paragraph(CurrencyService.format(stats.get('median_sale', 0), currency_code), body_style)
            ]
        ]
        
        t_kpi = Table(kpi_data, colWidths=[1.8 * inch, 1.8 * inch, 1.8 * inch, 1.8 * inch])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_light),
            ('BOX', (0, 0), (-1, -1), 0.5, border_color),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 12))
        
        # 3. Product Summary (Top 5)
        prod_list = stats.get('product_summary', [])
        if prod_list:
            elements.append(Paragraph(f"2. Top Product Categories Breakdown ({cur_info['code']})", section_style))
            p_rows = [[
                Paragraph("<b>Category / Product</b>", body_style),
                Paragraph(f"<b>Revenue ({cur_info['symbol']})</b>", body_style),
                Paragraph("<b>Units Sold</b>", body_style),
                Paragraph("<b>Share of Total</b>", body_style)
            ]]
            for p in prod_list[:6]:
                p_rows.append([
                    Paragraph(str(p.get('product', '')), body_style),
                    Paragraph(CurrencyService.format(p.get('sales', 0), currency_code), body_style),
                    Paragraph(f"{p.get('units', 0):,}", body_style),
                    Paragraph(f"{p.get('percentage', 0)}%", body_style)
                ])
            t_prod = Table(p_rows, colWidths=[2.6 * inch, 1.6 * inch, 1.5 * inch, 1.5 * inch])
            t_prod.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_prod)
            elements.append(Spacer(1, 12))
            
        # 4. Correlation Analysis
        corr = analysis_data.get('correlation_results', {})
        if corr.get('has_correlation') and corr.get('top_pairs'):
            elements.append(Paragraph("3. Correlation Analysis & Driver Identification", section_style))
            c_rows = [[
                Paragraph("<b>Variable Pair</b>", body_style),
                Paragraph("<b>Pearson r</b>", body_style),
                Paragraph("<b>Strength</b>", body_style),
                Paragraph("<b>Statistical Interpretation</b>", body_style)
            ]]
            for pair in corr.get('top_pairs', [])[:5]:
                c_rows.append([
                    Paragraph(f"{pair['var1']} vs {pair['var2']}", body_style),
                    Paragraph(f"{pair['correlation']:+.3f}", body_style),
                    Paragraph(f"{pair['strength']} {pair['direction']}", body_style),
                    Paragraph(pair['interpretation'], body_style)
                ])
            t_corr = Table(c_rows, colWidths=[2.2 * inch, 0.9 * inch, 1.3 * inch, 2.8 * inch])
            t_corr.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_corr)
            elements.append(Spacer(1, 6))
            elements.append(Paragraph("<i>* Methodological Note: Correlation measures linear co-movement, not direct causation.</i>", disclaimer_style))
            elements.append(Spacer(1, 12))

        # 5. Linear Regression Model
        if regression_data:
            elements.append(Paragraph("4. Linear Regression Model Evaluation", section_style))
            r_rows = [
                [
                    Paragraph("<b>Target Variable (y)</b>", body_style),
                    Paragraph(str(regression_data.get('target_variable', '')), body_style),
                    Paragraph("<b>R² Determination</b>", body_style),
                    Paragraph(f"{regression_data.get('r2_score', 0):.4f}", body_style)
                ],
                [
                    Paragraph("<b>Predictors (X)</b>", body_style),
                    Paragraph(", ".join(regression_data.get('predictor_variables', [])), body_style),
                    Paragraph("<b>RMSE Error</b>", body_style),
                    Paragraph(CurrencyService.format(regression_data.get('rmse', 0), currency_code), body_style)
                ],
                [
                    Paragraph("<b>Split Strategy</b>", body_style),
                    Paragraph(f"{regression_data.get('split_type', 'N/A').title()} ({int((1-regression_data.get('test_size',0.2))*100)}/{int(regression_data.get('test_size',0.2)*100)} split)", body_style),
                    Paragraph("<b>MAE Error</b>", body_style),
                    Paragraph(CurrencyService.format(regression_data.get('mae', 0), currency_code), body_style)
                ]
            ]
            t_reg = Table(r_rows, colWidths=[1.8 * inch, 2.4 * inch, 1.5 * inch, 1.5 * inch])
            t_reg.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_light),
                ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_reg)
            elements.append(Spacer(1, 6))
            
            # Coefficients breakdown
            coefs = regression_data.get('coefficients', {})
            intercept = regression_data.get('intercept', 0.0)
            coef_rows = [[
                Paragraph("<b>Predictor Variable</b>", body_style),
                Paragraph("<b>Estimated Coefficient (β)</b>", body_style),
                Paragraph("<b>Marginal Impact on Target</b>", body_style)
            ]]
            coef_rows.append([
                Paragraph("<b>Intercept (β0)</b>", body_style),
                Paragraph(f"{intercept:+.4f}", body_style),
                Paragraph("Baseline level when all predictors are zero", body_style)
            ])
            for feat, val in coefs.items():
                coef_rows.append([
                    Paragraph(str(feat), body_style),
                    Paragraph(f"{val:+.4f}", body_style),
                    Paragraph(f"Each 1-unit increase in '{feat}' changes target by {val:+.4f}", body_style)
                ])
            t_coef = Table(coef_rows, colWidths=[2.2 * inch, 1.8 * inch, 3.2 * inch])
            t_coef.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_coef)
            elements.append(Spacer(1, 12))

        # 6. Forecasts
        if forecast_data:
            elements.append(Paragraph(f"5. Sales Forecast Projections ({cur_info['code']})", section_style))
            f_type = forecast_data.get('forecast_type')
            if f_type == 'scenario':
                elements.append(Paragraph(
                    f"<b>Scenario Forecast Outcome:</b> {CurrencyService.format(forecast_data.get('predicted_value', 0), currency_code)} "
                    f"(95% Prediction Bounds: {CurrencyService.format(forecast_data.get('lower_bound_95', 0), currency_code)} – {CurrencyService.format(forecast_data.get('upper_bound_95', 0), currency_code)})",
                    body_style
                ))
            elif f_type == 'horizon':
                h_rows = [[
                    Paragraph("<b>Horizon Period</b>", body_style),
                    Paragraph(f"<b>Forecasted Sales ({cur_info['symbol']})</b>", body_style),
                    Paragraph(f"<b>Lower Bound 95% ({cur_info['symbol']})</b>", body_style),
                    Paragraph(f"<b>Upper Bound 95% ({cur_info['symbol']})</b>", body_style)
                ]]
                for res in forecast_data.get('results', [])[:8]:
                    h_rows.append([
                        Paragraph(str(res.get('period', '')), body_style),
                        Paragraph(CurrencyService.format(res.get('predicted_sales', 0), currency_code), body_style),
                        Paragraph(CurrencyService.format(res.get('lower_bound_95', 0), currency_code), body_style),
                        Paragraph(CurrencyService.format(res.get('upper_bound_95', 0), currency_code), body_style)
                    ])
                t_fc = Table(h_rows, colWidths=[2.2 * inch, 1.8 * inch, 1.6 * inch, 1.6 * inch])
                t_fc.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                    ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                    ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(t_fc)
            elements.append(Spacer(1, 12))

        # 7. Model Assumptions & Limitations
        elements.append(Paragraph("6. Assumptions, Data Requirements, and Limitations", section_style))
        assumptions_text = (
            "<b>Assumptions & Limitations:</b> Traditional Ordinary Least Squares (OLS) regression relies on linearity, "
            "residual independence, and homoscedasticity. Forecast projections assume historical trends and relationships "
            "persist into future horizons without drastic exogenous structural market shocks. Predictions requiring extrapolation "
            "beyond observed predictor ranges carry increased statistical variance."
        )
        elements.append(Paragraph(assumptions_text, disclaimer_style))
        
        doc.build(elements)
        
        if buffer is not None:
            buffer.seek(0)
            return buffer.getvalue()
        return None

    @staticmethod
    def generate_csv_summary(analysis_data, regression_data=None, forecast_data=None, currency_code='USD'):
        """
        Exports a comprehensive CSV data file with KPIs, regression metrics, and forecasts.
        Clearly indicates selected currency while preserving raw numerical precision.
        """
        cur_info = CurrencyService.get_currency(currency_code)
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Section 1: Overview
        writer.writerow(["=== SALES CORRELATION & REGRESSION FORECASTER EXPORT ==="])
        writer.writerow(["Title", analysis_data.get('title', '')])
        writer.writerow(["Dataset File", analysis_data.get('dataset_filename', '')])
        writer.writerow(["Currency", f"{cur_info['name']} ({cur_info['code']})"])
        writer.writerow(["Currency Symbol", cur_info['symbol']])
        writer.writerow(["Export Timestamp", datetime.now().isoformat()])
        writer.writerow([])
        
        # Section 2: KPIs
        stats = analysis_data.get('summary_stats', {})
        writer.writerow(["=== CORE SUMMARY KPIS ==="])
        writer.writerow(["Metric", f"Value ({cur_info['code']})"])
        writer.writerow(["Total Revenue", stats.get('total_revenue', 0)])
        writer.writerow(["Total Units Sold", stats.get('total_units', 0)])
        writer.writerow(["Average Sale", stats.get('average_sale', 0)])
        writer.writerow(["Median Sale", stats.get('median_sale', 0)])
        writer.writerow(["Standard Deviation", stats.get('std_sale', 0)])
        writer.writerow(["Sales Growth Rate (%)", stats.get('sales_growth_rate', 'N/A')])
        writer.writerow(["Date Range", stats.get('date_range_str', 'N/A')])
        writer.writerow([])
        
        # Section 3: Product Breakdown
        prod_list = stats.get('product_summary', [])
        if prod_list:
            writer.writerow(["=== PRODUCT CATEGORY BREAKDOWN ==="])
            writer.writerow(["Product / Category", f"Total Sales Revenue ({cur_info['code']})", "Units Sold", "Percentage Contribution (%)"])
            for p in prod_list:
                writer.writerow([p.get('product'), p.get('sales'), p.get('units'), p.get('percentage')])
            writer.writerow([])
            
        # Section 4: Regression Model
        if regression_data:
            writer.writerow(["=== LINEAR REGRESSION MODEL ==="])
            writer.writerow(["Target Variable", regression_data.get('target_variable')])
            writer.writerow(["Predictor Variables", "; ".join(regression_data.get('predictor_variables', []))])
            writer.writerow(["R-Squared (R2)", regression_data.get('r2_score')])
            writer.writerow([f"Mean Absolute Error (MAE) ({cur_info['code']})", regression_data.get('mae')])
            writer.writerow([f"Root Mean Squared Error (RMSE) ({cur_info['code']})", regression_data.get('rmse')])
            writer.writerow(["Split Type", regression_data.get('split_type')])
            writer.writerow(["Intercept", regression_data.get('intercept')])
            writer.writerow(["--- Feature Coefficients ---"])
            for feat, coef in regression_data.get('coefficients', {}).items():
                writer.writerow([feat, coef])
            writer.writerow([])
            
        # Section 5: Forecasts
        if forecast_data:
            writer.writerow(["=== FORECAST RESULTS ==="])
            f_type = forecast_data.get('forecast_type')
            if f_type == 'scenario':
                writer.writerow(["Forecast Type", "Scenario What-If"])
                writer.writerow([f"Predicted Sales ({cur_info['code']})", forecast_data.get('predicted_value')])
                writer.writerow([f"Lower 95% Bound ({cur_info['code']})", forecast_data.get('lower_bound_95')])
                writer.writerow([f"Upper 95% Bound ({cur_info['code']})", forecast_data.get('upper_bound_95')])
            elif f_type == 'horizon':
                writer.writerow(["Forecast Type", "Horizon Multi-Period"])
                writer.writerow(["Period", f"Forecasted Sales ({cur_info['code']})", f"Lower 95% Bound ({cur_info['code']})", f"Upper 95% Bound ({cur_info['code']})"])
                for r in forecast_data.get('results', []):
                    writer.writerow([r.get('period'), r.get('predicted_sales'), r.get('lower_bound_95'), r.get('upper_bound_95')])
            writer.writerow([])
            
        return output.getvalue()

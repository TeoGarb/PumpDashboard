from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.utils
import json
import math

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Process form data and calculate results
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        customers_to_swap = int(request.form['customers_to_swap'])
        new_customers_per_week = float(request.form['new_customers_per_week'])
        pumps_in_stock = int(request.form['pumps_in_stock'])
        pumps_on_order = int(request.form['pumps_on_order'])
        devices_returned_per_week = float(request.form['devices_returned_per_week'])
        extra_pumps_factor = float(request.form['extra_pumps_factor'])

        # Calculate statistics
        weeks = (end_date - start_date).days / 7
        pumps_to_swap_per_week = math.ceil(customers_to_swap / weeks)
        new_customer_pumps = math.ceil(new_customers_per_week * weeks)
        total_pumps_needed = customers_to_swap + new_customer_pumps

        # Calculate total pumps needed over the entire period
        total_pumps_needed_over_period = math.ceil(
            (pumps_to_swap_per_week + new_customers_per_week) * weeks
        )

        # Adjust for pumps already in stock
        additional_pumps_needed = max(0, total_pumps_needed_over_period - pumps_in_stock)

        # Calculate pumps to purchase per week, accounting for returns and extra factor
        pumps_to_purchase_per_week = math.ceil(
            (additional_pumps_needed / weeks) - devices_returned_per_week + extra_pumps_factor
        )

        cost_per_pump = 450
        rebate_per_pump = 25

        cost_per_week = pumps_to_purchase_per_week * cost_per_pump
        total_purchases = math.ceil(pumps_to_purchase_per_week * weeks)
        total_cost = total_purchases * cost_per_pump
        total_rebate = total_purchases * rebate_per_pump

        # Generate charts
        cumulative_cost_chart = generate_cumulative_cost_chart(weeks, cost_per_week)
        cumulative_comparison_chart = generate_cumulative_comparison_chart(
            weeks, pumps_to_purchase_per_week, pumps_to_swap_per_week, new_customers_per_week
        )
        pie_chart = generate_pie_chart(customers_to_swap, new_customer_pumps)

        return jsonify({
            'pumps_to_swap_per_week': round(pumps_to_swap_per_week, 2),
            'pumps_to_purchase_per_week': pumps_to_purchase_per_week,
            'cost_per_week': round(cost_per_week, 2),
            'total_purchases': total_purchases,
            'total_cost': round(total_cost, 2),
            'total_rebate': round(total_rebate, 2),
            'new_customer_pumps': round(new_customer_pumps, 2),
            'pumps_in_stock': pumps_in_stock,
            'additional_pumps_needed': additional_pumps_needed,
            'cumulative_cost_chart': json.dumps(cumulative_cost_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'cumulative_comparison_chart': json.dumps(cumulative_comparison_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'pie_chart': json.dumps(pie_chart, cls=plotly.utils.PlotlyJSONEncoder)
        })
    else:
        default_start_date = datetime.now().strftime('%Y-%m-%d')
        return render_template('index.html', default_start_date=default_start_date)

def generate_cumulative_cost_chart(weeks, cost_per_week):
    x = list(range(int(weeks) + 1))
    y = [i * cost_per_week for i in x]
    
    trace = go.Scatter(x=x, y=y, mode='lines+markers', name='Cumulative Cost')
    layout = go.Layout(title='Cumulative Purchase Cost Over Time',
                       xaxis=dict(title='Weeks'),
                       yaxis=dict(title='Cumulative Cost ($)'))
    
    return {'data': [trace], 'layout': layout}

def generate_cumulative_comparison_chart(weeks, pumps_to_purchase_per_week, pumps_to_swap_per_week, new_customers_per_week):
    x = list(range(int(weeks) + 1))
    y_purchases = [i * pumps_to_purchase_per_week for i in x]
    y_swaps = [i * pumps_to_swap_per_week for i in x]
    y_new_customers = [i * new_customers_per_week for i in x]
    
    trace_purchases = go.Scatter(x=x, y=y_purchases, mode='lines+markers', name='Cumulative Purchases')
    trace_swaps = go.Scatter(x=x, y=y_swaps, mode='lines+markers', name='Cumulative Swap Outs')
    trace_new_customers = go.Scatter(x=x, y=y_new_customers, mode='lines+markers', name='Cumulative New Customers')
    
    layout = go.Layout(title='Cumulative Purchases vs. Swap Outs vs. New Customers',
                       xaxis=dict(title='Weeks'),
                       yaxis=dict(title='Cumulative Count'))
    
    return {'data': [trace_purchases, trace_swaps, trace_new_customers], 'layout': layout}

def generate_pie_chart(customers_to_swap, new_customer_pumps):
    labels = ['Pumps Swapped Out', 'New Customers Added']
    values = [customers_to_swap, new_customer_pumps]
    
    trace = go.Pie(labels=labels, values=values, hole=0.3)
    layout = go.Layout(title='Ratio of Pumps Swapped Out vs New Customers Added')
    
    return {'data': [trace], 'layout': layout}

if __name__ == '__main__':
    app.run(debug=True,use_reloader=False)
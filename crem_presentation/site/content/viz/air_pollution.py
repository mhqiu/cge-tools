# -*- coding: utf-8 -*- #
import pandas as pd
from bokeh.embed import components
from bokeh.models import TextInput, CustomJS, ColumnDataSource, Line, Circle

from .charts import get_national_scenario_line_plot
from .constants import scenarios_colors as colors, scenarios, file_names
from .utils import get_js_array, env
from .data import get_df_and_strip_2007


def render_1():
    co2_plot, ap_plot, text = _get_1()
    template = env.get_template('viz/two_plots_with_selectors.html')
    script, div = components(
        dict(plot1=co2_plot, plot2=ap_plot, text=text),
        wrap_plot_info=False
    )
    return template.render(
        plot_script=script, plot_div=div,
        plot2_title="PM2.5 concentrations",
        prefix='dual',
    )


def render_2():
    plot, text = _get_2()
    template = env.get_template('viz/one_plot_with_selectors.html')
    script, div = components(dict(plot=plot, text=text), wrap_plot_info=False)
    return template.render(
        plot_script=script, plot_div=div,
        plot_title="PM2.5 concentrations",
        prefix='nh3',  # Adds a prefix for the checkboxes
    )


def _get_1():
    plot_width = 800
    ap_plot, ap_line_renderers = get_national_scenario_line_plot(
        parameter='PM25_conc',
        y_ticks=[20, 30, 40],
        plot_width=plot_width,
    )
    co2_plot, co2_line_renderers = get_national_scenario_line_plot(
        parameter='CO2_emi',
        y_ticks=[7000, 11000, 15000],
        plot_width=plot_width,
    )
    prefixed_line_renderers = {}
    for key in scenarios:
        prefixed_line_renderers['ap_%s' % key] = ap_line_renderers[key]
        prefixed_line_renderers['co2_%s' % key] = co2_line_renderers[key]

    line_array = get_js_array(prefixed_line_renderers.keys())
    code = '''
        var lines = %s,
            value = cb_obj.get('value'),
            highlight,
            glyph;

        value = value.replace(/(,$)/g, '');
        highlight = value.split(',');
        Bokeh.$.each(lines, function(key, line) {
            glyph = line.get('glyph');
            glyph.set('line_alpha', 0.1);
        });
        Bokeh.$.each(highlight, function(i, key) {
            function set_alpha(line) {
                glyph = line.get('glyph');
                glyph.set('line_alpha', 0.8);
            }
            set_alpha(lines['ap_' + key]);
            set_alpha(lines['co2_' + key]);
        });
    ''' % line_array

    callback = CustomJS(code=code, args=prefixed_line_renderers)
    text = TextInput(callback=callback)
    return (co2_plot, ap_plot, text)


def _get_2():
    parameter = 'PM25_conc'
    plot, line_renderers = get_national_scenario_line_plot(
        parameter=parameter,
        y_ticks=[25, 35, 45],
        plot_width=1200,
    )
    read_props = dict(usecols=['t', parameter])
    hit_renderers = []
    sources = {}
    nh3_scenarios = ['three_nh3', 'four_nh3', 'five_nh3']
    for scenario in nh3_scenarios:
        sources[scenario] = ColumnDataSource(
            get_df_and_strip_2007('../cecp-cop21-data/national/%s.csv' % file_names[scenario], read_props)
        )
    for scenario in nh3_scenarios:
        source = sources[scenario]
        if scenario == 'four_nh3':
            line_alpha = 0.8
        else:
            line_alpha = 0.1
        line = Line(
            x='t', y=parameter, line_color=colors[scenario], line_dash='dashed',
            line_width=4, line_cap='round', line_join='round', line_alpha=line_alpha
        )
        circle = Circle(
            x='t', y=parameter, size=8,
            line_color=colors[scenario], line_width=2,
            fill_color='white'
        )
        # invisible circle used for hovering
        hit_target = Circle(
            x='t', y=parameter, size=20,
            line_color=None,
            fill_color=None
        )
        hit_renderer = plot.add_glyph(source, hit_target)
        hit_renderers.append(hit_renderer)
        line_renderer = plot.add_glyph(source, line)
        line_renderers[scenario] = line_renderer
        plot.add_glyph(source, circle)

    all_scenarios = scenarios.copy()
    all_scenarios.extend(nh3_scenarios)
    line_array = get_js_array(all_scenarios)
    code = '''
        var lines = %s,
            value = cb_obj.get('value'),
            highlight,
            glyph;

        value = value.replace(/(,$)/g, '');
        highlight = value.split(',');
        Bokeh.$.each(lines, function(key, line) {
            glyph = line.get('glyph');
            glyph.set('line_alpha', 0.1);
        });
        Bokeh.$.each(highlight, function(i, key) {
            function set_alpha(line) {
                glyph = line.get('glyph');
                glyph.set('line_alpha', 0.8);
            }
            console.log(key)
            set_alpha(lines[key]);
            set_alpha(lines[key + '_nh3']);
        });
    ''' % line_array

    callback = CustomJS(code=code, args=line_renderers)
    text = TextInput(callback=callback)
    return (plot, text)
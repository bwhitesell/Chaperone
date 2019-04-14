function timelineChart(prediction, absAxis) {
    console.log('hi');
    var margin = { top: 20, right: 20, bottom: 50, left: 70 },
        width = 350,
        height = 350,
        parseTime = d3.timeParse("%Y-%m-%d"),
        timeValue = function(d) { return Array.apply(null, {length: N}).map(Function.call, Number); },
        dataValue = function (d) { return +d[prediction]; },
        color = "steelblue";

    // From https://bl.ocks.org/mbostock/5649592
    function transition(path) {
        path.transition()
            .duration(3000)
            .attrTween("stroke-dasharray", tweenDash);
    }
    function tweenDash() {
        var l = this.getTotalLength(),
            i = d3.interpolateString("0," + l, l + "," + l);
        return function (t) { return i(t); };
    }

    function chart(selection) {
        selection.each(function (data) {
            data = data.map(function (d, i) {
                return { time: timeValue(d), value: dataValue(d) };
            });
            var x = d3.scaleTime()
                .rangeRound([0, width - margin.left - margin.right])
                .domain(d3.extent(data, function(d) { return d.time; }));

            var y = d3.scaleLinear()
                    .rangeRound([height - margin.top - margin.bottom, 0])
                    .domain(d3.extent(data, function(d) {return d.value;}));

            if (absAxis==true) {
                var y = d3.scaleLinear()
                    .rangeRound([height - margin.top - margin.bottom, 0])
                    .domain([0, .4]);
            };
            var line = d3.line()
                .x(function(d) { return x(d.time); })
                .y(function(d) { return y(d.value); });

            var svg = d3.select(this).selectAll("svg").data([data]);
            var gEnter = svg.enter().append("svg").append("g");

            gEnter.append("path")
                .datum(data)
                .attr("class", "data")
                .attr("fill", "none")
                .attr("stroke", "#00C185")
                .attr("stroke-linejoin", "round")
                .attr("stroke-linecap", "round")
                .attr("stroke-width", 3);

            gEnter.append("g").attr("class", "Xaxis");
            gEnter.append("g").attr("class", "YAxis")
            gEnter.append("path")
                .attr("class", "data");

            var svg = selection.select("svg");
            svg.attr('width', width).attr('height', height);
            var g = svg.select("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            g.select("g.Xaxis")
                .attr("transform", "translate(0," + (height - margin.bottom) + ")")
                .call(d3.axisBottom(x)
                      .ticks(10)
                      .tickSize(-height)
                      .tickFormat(d3.timeFormat("%B  %Y")))
                .select(".domain")
                .remove();

            g.select("g.YAxis")
                .attr("class", "YAxis")
                .call(d3.axisLeft(y)
                    .tickSize(-width)
                    .ticks(6));


            g.select("path.data")
                .datum(data)
                .attr("d", line)
                .call(transition);


        });
    }



    chart.margin = function (_) {
        if (!arguments.length) return margin;
        margin = _;
        return chart;
    };

    chart.width = function (_) {
        if (!arguments.length) return width;
        width = _;
        return chart;
    };

    chart.height = function (_) {
        if (!arguments.length) return height;
        height = _;
        return chart;
    };

    chart.parseTime = function (_) {
        if (!arguments.length) return parseTime;
        parseTime = _;
        return chart;
    };

    chart.timeValue = function (_) {
        if (!arguments.length) return timeValue;
        timeValue = _;
        return chart;
    };

    chart.dataValue = function (_) {
        if (!arguments.length) return dataValue;
        dataValue = _;
        return chart;
    };


    return chart;
}
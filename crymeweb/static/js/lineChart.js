function SafetyChart(data, width, height) {
    var svgWidth = width, svgHeight = height;
    var margin = { top: 50, right: 50, bottom: 50, left: 50 };
    var width = svgWidth - margin.left - margin.right;
    var height = svgHeight - margin.top - margin.bottom;

    var svg = d3.select('svg')
     .attr("width", svgWidth)
     .attr("height", svgHeight);

    var g = svg.append("g")
    .attr("transform",
      "translate(" + margin.left + "," + margin.top + ")"
    );

    var x = d3.scaleLinear().rangeRound([0, width]);

    var y = d3.scaleLinear().rangeRound([height, 0]);

    function parseData(data) {
        var arr = [];
        counter = 0
        for (var i in data.estimate.positive_prob){
            arr.push(
                {
                    hour: counter,
                    value: data.estimate.positive_prob[i]
                });
            counter  = counter + 1;
        }
        return arr;
    }
    data = parseData(data);

    var line = d3.line()
       .x(function(d) { return x(d.hour)})
       .y(function(d) { return y(d.value)})
       x.domain(d3.extent(data, function(d) { return d.hour }));
       y.domain([0, .25]);

    g.append("g")
       .call(d3.axisBottom(x))
       .attr("transform", "translate(0," + height + ")")
       .append("text")
       .attr("fill", "#000")
       .attr("transform", "rotate(0)")
       .attr("text-anchor", "middle")
       .attr("x", (width / 2))
       .attr("y", 30)
       .attr("dx", "0.71em")
       .text("Hour");

    g.append("g")
       .call(d3.axisLeft(y))
       .append("text")
       .attr("fill", "#000")
       .attr("transform", "rotate(-90)")
       .attr("y", -45)
       .attr("x", -140)
       .attr("dy", "0.71em")
       .attr("text-anchor", "middle")
       .text("Safety");


    g.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("stroke-width", 1.5)
        .attr("d", line);


    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 260)
        .attr("y2", 260)
        .style("stroke", "rgb(124,252,0)")

    g.append("svg:text")
        .attr("x", width)
        .attr("y", 262)
        .text("Safe")
        .style("font-size", "10px")
        .style("font-family", "Merriweather Sans")

    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 225)
        .attr("y2", 225)
        .style("stroke", "rgb(248,230,4)")

    g.append("svg:text")
        .attr("x", width)
        .attr("y", 228)
        .text("Neutral")
        .style("font-size", "10px")
        .style("font-family", "Merriweather Sans")


    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 190)
        .attr("y2", 190)
        .style("stroke", "rgb(255,79,0)")

    g.append("svg:text")
        .attr("x", width- 70)
        .attr("y", 187)
        .text("Somewhat Dangerous")
        .style("font-size", "10px")
         .style("font-family", "Merriweather Sans")

    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 154)
        .attr("y2", 154)
        .style("stroke", "rgb(246,4,4)")

    g.append("svg:text")
        .attr("x", width - 20)
        .attr("y", 150)
        .text("Dangerous")
        .style("fill", "#9e379f")
        .style("font-size", "10px")
        .style("font-family", "Merriweather Sans")

}
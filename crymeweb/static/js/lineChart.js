function SafetyChart(data, width, height) {
    var svgWidth = width, svgHeight = height;
    var margin = { top: 50, right: 70, bottom: 50, left: 70 };
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
       .attr("color", "#9a9a9a")
       .attr("fill", "#9a9a9a")
       .attr("font-size", "15px")
       .attr("font-family", "Poppins,sans-serif")
       .attr("transform", "rotate(0)")
       .attr("text-anchor", "middle")
       .attr("x", (width / 2))
       .attr("y", 35)
       .attr("dx", "0.71em")
       .text("Hour");

    g.append("g")
       .call(d3.axisLeft(y))
       .append("text")
       .attr("color", "#9a9a9a")
       .attr("fill", "#9a9a9a")
       .attr("font-size", "15px")
       .attr("font-family", "Poppins,sans-serif")
       .attr("transform", "rotate(-90)")
       .attr("y", -55)
       .attr("x", -180)
       .attr("dy", "0.71em")
       .attr("text-anchor", "middle")
       .text("Safety Rating");


    g.append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "rgb(211, 70, 177)")
        .attr("stroke-linejoin", "round")
        .attr("stroke-linecap", "round")
        .attr("stroke-width", 1.5)
        .attr("d", line);


    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 370)
        .attr("y2", 370)
        .attr("stroke-width", ".17")
        .style("stroke", "rgb(211, 70, 177)")

    g.append("svg:text")
        .attr("x", width - 23)
        .attr("y", 365)
        .text("Safe")
        .style("font-size", "10px")
        .attr("fill", "#9a9a9a")
        .attr("color", "#9a9a9a")
        .style("font-family", "Merriweather Sans")

    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 318)
        .attr("y2", 318)
        .attr("stroke-width", ".17")
        .style("stroke", "rgb(211, 70, 177)")

    g.append("svg:text")
        .attr("x", width - 36)
        .attr("y", 313)
        .text("Neutral")
        .style("font-size", "10px")
        .attr("fill", "#9a9a9a")
        .attr("color", "#9a9a9a")
        .style("font-family", "Merriweather Sans")


    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 269)
        .attr("y2", 269)
        .attr("stroke-width", ".17")
        .style("stroke", "rgb(211, 70, 177)")

    g.append("svg:text")
        .attr("x", width - 105)
        .attr("y", 264)
        .text("Somewhat Dangerous")
        .attr("fill", "#9a9a9a")
        .attr("color", "#9a9a9a")
        .style("font-size", "10px")
        .style("font-family", "Merriweather Sans")

    g.append("svg:line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", 218)
        .attr("y2", 218)
        .attr("stroke-width", ".17")
        .style("stroke", "rgb(211, 70, 177)")

    g.append("svg:text")
        .attr("x", width - 50)
        .attr("y", 213)
        .text("Dangerous")
        .attr("fill", "#9a9a9a")
        .attr("color", "#9a9a9a")
        .style("font-size", "10px")
        .style("font-family", "Merriweather Sans")

}
function myGeeks() {
  
    // Create a progress element
    var g = document.createElement("progress");

    // Set the value of progress element
    g.setAttribute("value", "57");

    // Set the maximum value of progress element
    g.setAttribute("max", "100");

    // Get the value of progress element
    document.getElementById("GFG").appendChild(g);
} 
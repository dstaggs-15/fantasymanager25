<!DOCTYPE html>
<html lang="en">
<head>
    <title>VORP Analysis</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header><h1>Value Over Replacement Player (VORP)</h1><nav><a href="index.html">Home</a></nav></header>
    <main>
        <div class="report-card">
            <h3>How to Read This Page</h3>
            <p>
                <strong>VORP (Value Over Replacement Player)</strong> measures a player's value against an average, waiver-wire level player at the same position. A higher VORP score indicates a greater positional advantage. This is useful in drafts because it highlights players at scarce positions (like TE) who provide more value than a similarly-ranked player at a deep position (like WR).
            </p>
        </div>

        <h2>Player Comparison</h2>
        <div class="report-grid">
            <div class="report-card">
                <label for="player1-search">Player 1</label>
                <input type="text" id="player1-search" list="player-list" placeholder="Search for a player...">
            </div>
            <div class="report-card">
                <label for="player2-search">Player 2</label>
                <input type="text" id="player2-search" list="player-list" placeholder="Search for a player...">
            </div>
        </div>
        <div id="comparison-results"></div>
        
        <h2 id="report-title">Loading Report...</h2>
        <div class="table-container">
            <table id="vorp-table"></table>
        </div>

        <datalist id="player-list"></datalist>
    </main>
    <script src="vorp.js"></script>
</body>
</html>

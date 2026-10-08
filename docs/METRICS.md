# Forecasting Metrics

Lonely Planner uses **MAE%**, **Bias%**, and **Score** as its core accuracy metrics, following SupChains / Nicolas Vandeput best practices.

## The Three Metrics

### MAE% (Mean Absolute Error %)

**Formula:** `MAE% = sum(|error|) / sum(actual) × 100`

Where `error = forecast - actual`

**Interpretation:** MAE% measures the average magnitude of forecast errors as a percentage of total actual demand. Lower is better.

**Example:** If MAE% = 15%, the forecast misses by an average of 15% of total demand.

### Bias% (Forecast Bias %)

**Formula:** `Bias% = sum(error) / sum(actual) × 100`

**Interpretation:** Bias% measures systematic over-forecasting (positive bias) or under-forecasting (negative bias). Zero is ideal.

**Example:** If Bias% = +10%, the forecast systematically over-predicts by 10% of total demand. If Bias% = -5%, it under-predicts by 5%.

### Score

**Formula:** `Score = MAE% + |Bias%|`

**Interpretation:** Score combines accuracy and bias into a single metric. Lower is better. It penalizes both inaccuracy (MAE%) and systematic bias.

**Example:** If MAE% = 12% and Bias% = -4%, then Score = 12 + 4 = 16.

## Why These Metrics?

1. **Weighted by total demand:** MAE% and Bias% weight errors by actual demand volume, focusing attention where it matters most.

2. **Scale-independent:** Unlike absolute MAE, MAE% can be compared across different products and time periods.

3. **Directional information:** Bias% reveals whether forecasts are consistently high or low, which matters for inventory decisions.

4. **Single combined metric:** Score provides a single number for ranking and optimization, balancing accuracy and bias.

## Why NOT MAPE?

**MAPE (Mean Absolute Percentage Error)** is **not implemented** in Lonely Planner, following SupChains guidance.

**Problems with MAPE:**

1. **Undefined for zero actuals:** Division by zero when actual demand is zero
2. **Asymmetric:** Over-forecasts and under-forecasts are penalized differently
3. **Biased toward under-forecasting:** Models optimized for MAPE systematically under-forecast
4. **Extreme values:** Small actuals create huge percentage errors that dominate the metric

**Better alternatives:** MAE% (weighted by total demand) and weighted MAE (weighted by value/volume).

## Lag-1 vs Cumulative

### Lag-1 Metrics

**Lag-1** measures one-period-ahead forecast accuracy. This is the most immediate test of a forecasting method.

**Use case:** Evaluate short-term forecast quality and responsiveness to recent demand changes.

### Cumulative Metrics

**Cumulative** metrics measure accuracy over a rolling horizon (e.g., cumulative 3-month or 6-month forecasts).

**Use case:** Evaluate forecast accuracy over the risk horizon relevant to inventory and supply decisions.

**Example:** For a product with a 3-month lead time, cumulative 3-month accuracy matters more than lag-1 accuracy for planning purposes.

## References

- Nicolas Vandeput, *Demand Forecasting Best Practices* (2023)
- SupChains: [MAE% and Bias% article](https://medium.com/supchains)
- VN1 Forecasting Competition learnings (2025)

# Adoption of Coding Agents in Machine Learning Projects

This repository is the companion package for the register report: Adoption of Coding Agents in Machine Learning Projects.

## Github project mining

- Queries
- Filter
- Tool

## Agent detection

- Tool
- Agent supported by default
- New agents

## Sample size 
To propoerly compute the a priori sample size using G\*Power we had to convert the r type effect of Rrb to d type effect (G\*Power uses dz effect).
We used the convertion formula [1,2] implemented in [this R script](effect_size_convertion.R/).
For an effect of 0.1 in r that gives us 0.2010076 in d.
We used this d value in G\*Power.
The complete settings used and result are in [this file](G_Power_power.txt/).

1. Aaron, B., Kromrey, J. D., & Ferron, J. (1998). Equating.
2. Borenstein, M., Cooper, H., Hedges, L., & Valentine, J. (2009). Effect sizes for continuous data. The handbook of research synthesis and meta-analysis, 2, 221-235.
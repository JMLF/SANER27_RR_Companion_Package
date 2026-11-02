r_to_d <- function(r, n1 = NULL, n2 = NULL) {
  if (any(abs(r) >= 1)) stop("r must be strictly between -1 and 1")
  a <- if (is.null(n1) || is.null(n2)) 4 else (n1 + n2)^2 / (n1 * n2)
  r * sqrt(a) / sqrt(1 - r^2)
}

r_to_d(0.1)                 # equal groups (a = 4) -> ~0.50
#r_to_d(0.2425, n1 = 30, n2 = 70)  # unequal groups
#r_to_d(c(0.1, 0.3, 0.5), 40, 60)  # works on vectors too
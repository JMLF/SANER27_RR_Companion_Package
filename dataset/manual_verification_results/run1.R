# In this script we compute inter annotator agreement with Cohen Kappa and PABAK
# Also we compute the precision as the proportion of sampled repositories labeled as ML projects, together with its 95% Wilson score interval

valid_labels <- c("ml_project", "not_ml_project")

read_annot <- function(path) {
  df <- read.csv(path, sep = ";", stringsAsFactors = FALSE,
                 strip.white = TRUE, na.strings = c("", "NA"))
  df <- df[, c("Repository", "Annotator", "Label")]
  df$Label <- trimws(tolower(df$Label))
  
  bad <- !is.na(df$Label) & !(df$Label %in% valid_labels)
  if (any(bad)) {
    cat(sprintf("%s: %d invalid label(s) set to NA\n", basename(path), sum(bad)))
    print(df[bad, c("Repository", "Label")], row.names = FALSE)
  }
  df$Label[bad] <- NA
  df
}


a1 <- read_annot("dataset/manual_verification_results/author_1_manual_verification.csv")  
a2 <- read_annot("dataset/manual_verification_results/author_2_manual_verification.csv")


m <- merge(a1[, c("Repository", "Label")], a2[, c("Repository", "Label")],
           by = "Repository", suffixes = c("_1", "_2"))
m <- m[complete.cases(m), ]          # drop repos either annotator left unlabeled
cat("Items compared:", nrow(m), "\n")


lev <- sort(union(m$Label_1, m$Label_2))
tab <- table(Annotator1 = factor(m$Label_1, levels = lev),
             Annotator2 = factor(m$Label_2, levels = lev))
print(tab)

install.packages(c("epiR", "irr"))
library(epiR)
library(irr)

# ---- Kappa and PABAK via epiR (needs the 2x2 table tab) ----
res <- epi.kappa(tab, method = "cohen", alternative = "greater", conf.level = 0.95)

print(res$prop.agree)   # observed and expected agreement
print(res$kappa)        # Cohen's kappa: est, lower, upper
print(res$pabak)        # PABAK: est, lower, upper

# ---- Cross-check kappa with irr (z statistic and p-value) ----
print(kappa2(m[, c("Label_1", "Label_2")], weight = "unweighted"))


# Now let compute precision
install.packages("binom")
library(binom)

# ---- Read the consensus labels ----
cons <- read.csv("dataset/manual_verification_results/consensus_manual_verification.csv", sep = ";", stringsAsFactors = FALSE,
                 strip.white = TRUE, na.strings = c("", "NA"))
cons <- cons[, c("Repository", "Label")]
cons$Label <- trimws(tolower(cons$Label))

bad <- !is.na(cons$Label) & !(cons$Label %in% valid_labels)
if (any(bad)) {
  cat(sprintf("%d invalid label(s) set to NA\n", sum(bad)))
  print(cons[bad, ], row.names = FALSE)
}
cons$Label[bad] <- NA
stopifnot(!anyDuplicated(cons$Repository))

cons <- cons[!is.na(cons$Label), ]

# ---- Precision with Wilson 95% CI ----
x <- sum(cons$Label == "ml_project")   # repositories labeled as ML projects
n <- nrow(cons)                        # repositories with a valid label

prec <- binom.confint(x, n, conf.level = 0.95, methods = "wilson")
print(prec)

cat(sprintf("Precision: %.3f (%d/%d), 95%% Wilson CI [%.3f, %.3f]\n",
            prec$mean, x, n, prec$lower, prec$upper))


# Referee round 3: iETS benchmark for the intermittent-demand process D8.
#
# Reads results/round3/d8_count_series.csv (written by L4_d8_count_benchmarks.py; one row per
# series x time point with columns n, rep, t, y; the file holds the CONTEXT only) and fits
#   smooth::adam(y, model = "MNN", occurrence = "auto")
# i.e. the iETS(M,N,N) model of Svetunkov & Boylan with automatic selection of the occurrence
# model (fixed / odds-ratio / inverse-odds-ratio / direct / general, by information criterion)
# and the default size distribution (Gamma mixture). Forecasts h = 12 with
#   forecast(fit, h = 12, interval = "simulated", level = 0.1..0.9, side = "upper", nsim = 10000)
# so the "Upper bound (q)" columns are the q-quantiles of the simulated predictive distribution.
# The point forecast recorded is fit$mean (the conditional expectation, occurrence x size).
#
# Output: results/round3/d8_count_iets_forecasts.csv (one row per series x horizon step).
# Runs on 4 PSOCK workers. Each series is seeded (seed = 1e5 * n + rep) so the simulated
# quantiles are reproducible. Every fit is wrapped in tryCatch and failures are recorded.

suppressPackageStartupMessages({ library(parallel) })

args <- commandArgs(trailingOnly = FALSE)
this <- sub("^--file=", "", args[grep("^--file=", args)])
root <- normalizePath(file.path(dirname(this), ".."), winslash = "/")
inp  <- file.path(root, "results", "round3", "d8_count_series.csv")
outp <- file.path(root, "results", "round3", "d8_count_iets_forecasts.csv")
H <- 12L
LV <- seq(0.1, 0.9, by = 0.1)

d <- read.csv(inp)
d <- d[order(d$n, d$rep, d$t), ]
key <- paste(d$n, d$rep, sep = "|")
ctx <- split(d$y, key)
jobs <- names(ctx)

fit_one <- function(k, ctx, H, LV) {
  parts <- as.integer(strsplit(k, "|", fixed = TRUE)[[1]])
  y <- ctx[[k]]
  set.seed(100000L * parts[1] + parts[2])
  t0 <- proc.time()[["elapsed"]]
  res <- tryCatch({
    fit <- smooth::adam(y, model = "MNN", occurrence = "auto")
    f <- forecast(fit, h = H, interval = "simulated", level = LV, side = "upper", nsim = 10000)
    q <- matrix(as.numeric(f$upper), nrow = H)
    if (any(!is.finite(q)) || any(!is.finite(as.numeric(f$mean)))) stop("non-finite forecast")
    list(mean = as.numeric(f$mean), q = q, model = smooth::modelType(fit),
         occ = fit$occurrence$occurrence, err = "")
  }, error = function(e) list(mean = rep(NA_real_, H), q = matrix(NA_real_, H, length(LV)),
                              model = "", occ = "", err = conditionMessage(e)))
  el <- proc.time()[["elapsed"]] - t0
  out <- data.frame(n = parts[1], rep = parts[2], h = seq_len(H), mean = res$mean,
                    res$q, model = res$model, occurrence = if (is.null(res$occ)) "" else res$occ,
                    error = res$err, secs = el)
  names(out)[5:13] <- sprintf("q%02d", round(100 * LV))
  out
}

cl <- makeCluster(4L)
invisible(clusterEvalQ(cl, suppressPackageStartupMessages({ library(smooth) })))
t0 <- Sys.time()
res <- parLapply(cl, jobs, fit_one, ctx = ctx, H = H, LV = LV)
stopCluster(cl)
res <- do.call(rbind, res)
write.csv(res, outp, row.names = FALSE)
cat(sprintf("iETS: %d series, %d failures, %.1f s wall\n", length(jobs),
            sum(res$error[res$h == 1] != ""), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("smooth %s, greybox %s, %s\n", packageVersion("smooth"), packageVersion("greybox"),
            R.version.string))
print(table(res$occurrence[res$h == 1]))

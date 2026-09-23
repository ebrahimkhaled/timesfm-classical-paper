# Referee round 2, R cross-check, step 2: fit R's `forecast` package to the D4/D5 series.
#
# For every series in results/round2/r_check_series.csv (written by L2_export_series.py):
#   y <- ts(context, frequency = 12)
#   forecast::auto.arima(y)          (all defaults)
#   forecast::ets(y)                 (all defaults)
#   forecast::thetaf(y, h = 12)      (all defaults)
# and forecast h = 12. Records the 12 point forecasts, the chosen model string, whether the
# chosen form is seasonal (ets: seasonal component != "N"; arima: any of P, D, Q > 0 from
# arimaorder()), fit time, and any error (each fit is wrapped in tryCatch).
#
# Output: results/round2/r_forecast_check_forecasts.csv (one row per series x method).
# Runs on 4 PSOCK workers (parLapply); the seeding is irrelevant (all fits are deterministic).

suppressPackageStartupMessages({ library(forecast); library(parallel) })

args <- commandArgs(trailingOnly = FALSE)
this <- sub("^--file=", "", args[grep("^--file=", args)])
root <- normalizePath(file.path(dirname(this), ".."), winslash = "/")
inp  <- file.path(root, "results", "round2", "r_check_series.csv")
outp <- file.path(root, "results", "round2", "r_forecast_check_forecasts.csv")
H <- 12L

d <- read.csv(inp, stringsAsFactors = FALSE)
d <- d[order(d$dgp, d$n, d$rep, d$t), ]
key <- paste(d$dgp, d$n, d$rep, sep = "|")
ctx <- split(d$y[d$part == "context"], key[d$part == "context"])
jobs <- names(ctx)

fit_one <- function(k, ctx, H) {
  suppressPackageStartupMessages(library(forecast))
  y  <- ts(ctx[[k]], frequency = 12)
  id <- strsplit(k, "|", fixed = TRUE)[[1]]
  one <- function(method, expr) {
    t0 <- proc.time()[["elapsed"]]
    r <- tryCatch({
      res <- expr()
      c(list(status = "ok", error = ""), res)
    }, error = function(e) list(status = "fail", error = conditionMessage(e),
                                model = NA_character_, seasonal = NA, f = rep(NA_real_, H)))
    f <- as.numeric(r$f)
    if (length(f) != H || any(!is.finite(f))) {
      if (r$status == "ok") { r$status <- "fail"; r$error <- "non-finite or wrong-length forecast" }
      f <- c(f, rep(NA_real_, H))[seq_len(H)]
    }
    out <- data.frame(dgp = id[1], n = as.integer(id[2]), rep = as.integer(id[3]),
                      method = method, status = r$status, model = r$model,
                      seasonal = r$seasonal, secs = proc.time()[["elapsed"]] - t0,
                      error = gsub("[\r\n]+", " ", r$error), stringsAsFactors = FALSE)
    fm <- matrix(f, nrow = 1, dimnames = list(NULL, paste0("f", seq_len(H))))
    cbind(out, as.data.frame(fm))
  }
  rbind(
    one("R_auto.arima", function() {
      m <- auto.arima(y)
      o <- arimaorder(m)  # p d q [P D Q Frequency]
      seas <- length(o) >= 6 && any(o[c("P", "D", "Q")] > 0)
      list(model = forecast:::arima.string(m, padding = FALSE), seasonal = seas,
           f = forecast(m, h = H)$mean)
    }),
    one("R_ets", function() {
      m <- ets(y)
      list(model = m$method, seasonal = m$components[3] != "N",
           f = forecast(m, h = H)$mean)
    }),
    one("R_thetaf", function() {
      fc <- thetaf(y, h = H)
      list(model = "thetaf", seasonal = NA, f = fc$mean)
    })
  )
}

t0 <- Sys.time()
cl <- makeCluster(4L)
res <- parLapply(cl, jobs, fit_one, ctx = ctx, H = H)
stopCluster(cl)
out <- do.call(rbind, res)
write.csv(out, outp, row.names = FALSE)
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("forecast %s | %d series x 3 methods | failures %d | wall %.1f s\n",
            as.character(packageVersion("forecast")), length(jobs), sum(out$status != "ok"), el))
cat("wrote", outp, "\n")

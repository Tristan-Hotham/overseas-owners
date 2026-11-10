"""Poisson pseudo-maximum likelihood with one set of fixed effects, concentrated out, and cluster-robust standard errors.

For a Poisson model y_i ~ exp(a_g + x_i b + offset_i) the group effects have the closed form
a_g = log(sum_g y / sum_g exp(x b + offset)), so Newton steps run on b alone. Scores are (y - mu)(x - xbar_g), with xbar_g
the mu-weighted group mean, and the Hessian is sum_g sum_i mu_i (x_i - xbar_g)(x_i - xbar_g)'. Clusters must nest the
fixed-effect groups (here clusters are districts and the groups are districts or district x jurisdiction group).
Checked against statsmodels GLM with dummies in 02_analysis.py."""
import numpy as np
import pandas as pd


def _gsum(v, g, G):
    out = np.zeros((G,) + v.shape[1:])
    np.add.at(out, g, v)
    return out


def fepois(y, X, offset, groups, clusters, tol=1e-10, maxit=100):
    y = np.asarray(y, float); X = np.asarray(X, float); off = np.asarray(offset, float)
    g, gi = np.unique(np.asarray(groups), return_inverse=True); G = len(g)
    # drop groups with no events (their FE is -inf and they carry no information)
    ys = _gsum(y, gi, G)
    keep = ys[gi] > 0
    y, X, off, gi, cl = y[keep], X[keep], off[keep], gi[keep], np.asarray(clusters)[keep]
    _, gi = np.unique(gi, return_inverse=True); G = gi.max() + 1
    ys = _gsum(y, gi, G)
    b = np.zeros(X.shape[1])
    for it in range(maxit):
        eta = X @ b + off
        e = np.exp(eta - eta.max())
        a = np.log(ys) - np.log(_gsum(e, gi, G)) - eta.max()
        mu = np.exp(eta + a[gi])
        musum = _gsum(mu, gi, G)
        xbar = _gsum(mu[:, None] * X, gi, G) / musum[:, None]
        Xd = X - xbar[gi]
        score = Xd.T @ (y - mu)
        H = (Xd * mu[:, None]).T @ Xd
        step = np.linalg.solve(H, score)
        b = b + step
        if np.max(np.abs(step)) < tol:
            break
    eta = X @ b + off
    e = np.exp(eta - eta.max())
    a = np.log(ys) - np.log(_gsum(e, gi, G)) - eta.max()
    mu = np.exp(eta + a[gi])
    xbar = _gsum(mu[:, None] * X, gi, G) / _gsum(mu, gi, G)[:, None]
    Xd = X - xbar[gi]
    H = (Xd * mu[:, None]).T @ Xd
    s = Xd * (y - mu)[:, None]
    c, ci = np.unique(cl, return_inverse=True); C = len(c)
    S = _gsum(s, ci, C)
    meat = S.T @ S
    Hi = np.linalg.inv(H)
    n, k = len(y), X.shape[1]
    V = Hi @ meat @ Hi * (C / (C - 1))
    se = np.sqrt(np.diag(V))
    return {"b": b, "se": se, "V": V, "n": int(n), "clusters": int(C), "groups": int(G), "dropped": int((~keep).sum()),
            "iter": it + 1}


def irr_table(fit, names, scale=1.0):
    b, se = fit["b"] * scale, fit["se"] * scale
    return pd.DataFrame({"term": names, "b": b, "se": se, "irr": np.exp(b), "lo": np.exp(b - 1.96 * se),
                         "hi": np.exp(b + 1.96 * se), "z": b / se})


def fenb(y, X, offset, groups, clusters, alpha, tol=1e-9, maxit=200):
    """NB2 regression (log link, fixed alpha) with one set of fixed effects by IRLS with weighted within-group demeaning
    (Frisch-Waugh-Lovell), cluster-robust sandwich standard errors. Returns b, se, log-likelihood."""
    from scipy.special import gammaln
    y = np.asarray(y, float); X = np.asarray(X, float); off = np.asarray(offset, float)
    _, gi = np.unique(np.asarray(groups), return_inverse=True); G = gi.max() + 1
    ys = _gsum(y, gi, G); keep = ys[gi] > 0
    y, X, off, gi, cl = y[keep], X[keep], off[keep], gi[keep], np.asarray(clusters)[keep]
    _, gi = np.unique(gi, return_inverse=True); G = gi.max() + 1
    # start: group log rates
    a = np.log(_gsum(y, gi, G) / _gsum(np.exp(off), gi, G))
    eta = off + a[gi]; b = np.zeros(X.shape[1])
    for it in range(maxit):
        mu = np.exp(eta)
        w = mu / (1 + alpha * mu)
        z = eta - off + (y - mu) / mu
        ws = _gsum(w, gi, G)
        zb = _gsum(w * z, gi, G) / ws; Xb = _gsum(w[:, None] * X, gi, G) / ws[:, None]
        Xd = X - Xb[gi]; zd = z - zb[gi]
        bn = np.linalg.solve((Xd * w[:, None]).T @ Xd, (Xd * w[:, None]).T @ zd)
        a = zb - Xb @ bn
        eta_n = off + X @ bn + a[gi]
        done = np.max(np.abs(bn - b)) < tol
        b, eta = bn, eta_n
        if done:
            break
    mu = np.exp(eta)
    w = mu / (1 + alpha * mu); ws = _gsum(w, gi, G)
    Xd = X - (_gsum(w[:, None] * X, gi, G) / ws[:, None])[gi]
    H = (Xd * w[:, None]).T @ Xd
    s = Xd * ((y - mu) / (1 + alpha * mu))[:, None]
    c, ci = np.unique(cl, return_inverse=True); C = len(c)
    S = _gsum(s, ci, C)
    Hi = np.linalg.inv(H)
    V = Hi @ (S.T @ S) @ Hi * (C / (C - 1))
    r = 1 / alpha
    ll = float(np.sum(gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu))))
    return {"b": b, "se": np.sqrt(np.diag(V)), "ll": ll, "n": int(len(y)), "clusters": int(C), "iter": it + 1}

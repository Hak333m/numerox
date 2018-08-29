from nose.tools import ok_

import numpy as np

import numerox as nx


def test_splitter_overlap():
    "prediction data should not overlap"
    d = nx.play_data()
    splitters = [nx.TournamentSplitter(d),
                 nx.FlipSplitter(d),
                 nx.ValidationSplitter(d),
                 nx.CheatSplitter(d),
                 nx.CVSplitter(d),
                 nx.LoocvSplitter(d),
                 nx.IgnoreEraCVSplitter(d, tournament=1),
                 nx.SplitSplitter(d, fit_fraction=0.5),
                 nx.ConsecutiveCVSplitter(d)]
    for splitter in splitters:
        predict_ids = []
        for dfit, dpredict in splitter:
            predict_ids.extend(dpredict.ids.tolist())
        ok_(len(predict_ids) == len(set(predict_ids)), "ids overlap")


def test_splitter_reset():
    "splitter reset should not change results"
    d = nx.play_data()
    splitters = [nx.TournamentSplitter(d),
                 nx.FlipSplitter(d),
                 nx.ValidationSplitter(d),
                 nx.CheatSplitter(d),
                 nx.CVSplitter(d),
                 nx.LoocvSplitter(d),
                 nx.IgnoreEraCVSplitter(d, tournament=2),
                 nx.SplitSplitter(d, fit_fraction=0.5),
                 nx.ConsecutiveCVSplitter(d)]
    for splitter in splitters:
        ftups = [[], []]
        ptups = [[], []]
        for i in range(2):
            for dfit, dpredict in splitter:
                ftups[i].append(dfit)
                ptups[i].append(dpredict)
            splitter.reset()
        ok_(ftups[0] == ftups[1], "splitter reset changed fit split")
        ok_(ptups[0] == ptups[1], "splitter reset changed predict split")


def test_cvsplitter_kfold():
    "make sure cvsplitter runs k folds"
    d = nx.play_data()
    for k in (2, 3):
        splitter = nx.CVSplitter(d, kfold=k)
        count = 0
        for dfit, dpredict in splitter:
            count += 1
        ok_(count == k, "CVSplitter iterated through wrong number of folds")


def test_loocvsplitter():
    "test loocvsplitter"
    d = nx.play_data()['train']
    splitter = nx.LoocvSplitter(d)
    count = 0
    for dfit, dpre in splitter:
        count += 1
        eras = dfit.unique_era().tolist()
        era = dpre.unique_era().tolist()
        ok_(isinstance(eras, list), "expecting a list")
        ok_(isinstance(era, list), "expecting a list")
        ok_(len(era) == 1, "expecting a single era")
        ok_(era not in eras, "did not hold out era")
    k = d.unique_era().size
    ok_(count == k, "LoocvSplitter iterated through wrong number of folds")


def test_rollsplitter():
    "make sure rollsplitter has no overlaps"
    d = nx.play_data()
    splitter = nx.RollSplitter(d, fit_window=15, predict_window=10, step=15)
    for dfit, dpre in splitter:
        fera = dfit.unique_era()
        pera = dpre.unique_era()
        tera = np.unique(np.concatenate((fera, pera)))
        nfit = fera.size
        npre = pera.size
        ntot = tera.size
        ok_(nfit + npre == ntot, "RollSplitter has era overalp")

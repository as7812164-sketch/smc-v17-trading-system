.class Landroidx/lifecycle/LiveData$LifecycleBoundObserver;
.super Landroidx/lifecycle/m;
.source "SourceFile"

# interfaces
.implements Landroidx/lifecycle/h;


# annotations
.annotation system Ldalvik/annotation/Signature;
    value = {
        "Landroidx/lifecycle/m;",
        "Landroidx/lifecycle/h;"
    }
.end annotation


# instance fields
.field final b:Landroidx/lifecycle/j;


# virtual methods
.method public h(Landroidx/lifecycle/j;Landroidx/lifecycle/e$a;)V
    .locals 1

    .line 1
    iget-object p1, p0, Landroidx/lifecycle/LiveData$LifecycleBoundObserver;->b:Landroidx/lifecycle/j;

    .line 2
    .line 3
    invoke-interface {p1}, Landroidx/lifecycle/j;->a()Landroidx/lifecycle/e;

    .line 4
    .line 5
    .line 6
    move-result-object p1

    .line 7
    invoke-virtual {p1}, Landroidx/lifecycle/e;->b()Landroidx/lifecycle/e$b;

    .line 8
    .line 9
    .line 10
    move-result-object p1

    .line 11
    sget-object p2, Landroidx/lifecycle/e$b;->a:Landroidx/lifecycle/e$b;

    .line 12
    .line 13
    const/4 v0, 0x0

    .line 14
    if-eq p1, p2, :cond_1

    .line 15
    .line 16
    :goto_0
    if-eq v0, p1, :cond_0

    .line 17
    .line 18
    invoke-virtual {p0}, Landroidx/lifecycle/LiveData$LifecycleBoundObserver;->i()Z

    .line 19
    .line 20
    .line 21
    move-result p2

    .line 22
    invoke-virtual {p0, p2}, Landroidx/lifecycle/m;->d(Z)V

    .line 23
    .line 24
    .line 25
    iget-object p2, p0, Landroidx/lifecycle/LiveData$LifecycleBoundObserver;->b:Landroidx/lifecycle/j;

    .line 26
    .line 27
    invoke-interface {p2}, Landroidx/lifecycle/j;->a()Landroidx/lifecycle/e;

    .line 28
    .line 29
    .line 30
    move-result-object p2

    .line 31
    invoke-virtual {p2}, Landroidx/lifecycle/e;->b()Landroidx/lifecycle/e$b;

    .line 32
    .line 33
    .line 34
    move-result-object p2

    .line 35
    move-object v0, p1

    .line 36
    move-object p1, p2

    .line 37
    goto :goto_0

    .line 38
    :cond_0
    return-void

    .line 39
    :cond_1
    throw v0
.end method

.method i()Z
    .locals 2

    .line 1
    iget-object v0, p0, Landroidx/lifecycle/LiveData$LifecycleBoundObserver;->b:Landroidx/lifecycle/j;

    .line 2
    .line 3
    invoke-interface {v0}, Landroidx/lifecycle/j;->a()Landroidx/lifecycle/e;

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    invoke-virtual {v0}, Landroidx/lifecycle/e;->b()Landroidx/lifecycle/e$b;

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    sget-object v1, Landroidx/lifecycle/e$b;->d:Landroidx/lifecycle/e$b;

    .line 12
    .line 13
    invoke-virtual {v0, v1}, Landroidx/lifecycle/e$b;->b(Landroidx/lifecycle/e$b;)Z

    .line 14
    .line 15
    .line 16
    move-result v0

    .line 17
    return v0
.end method

.class Landroidx/fragment/app/FragmentManager$6;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Landroidx/lifecycle/h;


# instance fields
.field final synthetic a:Ljava/lang/String;

.field final synthetic b:Landroidx/lifecycle/e;


# virtual methods
.method public h(Landroidx/lifecycle/j;Landroidx/lifecycle/e$a;)V
    .locals 2

    .line 1
    sget-object p1, Landroidx/lifecycle/e$a;->ON_START:Landroidx/lifecycle/e$a;

    .line 2
    .line 3
    const/4 v0, 0x0

    .line 4
    if-ne p2, p1, :cond_1

    .line 5
    .line 6
    invoke-static {v0}, Landroidx/fragment/app/a;->a(Landroidx/fragment/app/a;)Ljava/util/Map;

    .line 7
    .line 8
    .line 9
    move-result-object p1

    .line 10
    iget-object v1, p0, Landroidx/fragment/app/FragmentManager$6;->a:Ljava/lang/String;

    .line 11
    .line 12
    invoke-interface {p1, v1}, Ljava/util/Map;->get(Ljava/lang/Object;)Ljava/lang/Object;

    .line 13
    .line 14
    .line 15
    move-result-object p1

    .line 16
    check-cast p1, Landroid/os/Bundle;

    .line 17
    .line 18
    if-nez p1, :cond_0

    .line 19
    .line 20
    goto :goto_0

    .line 21
    :cond_0
    throw v0

    .line 22
    :cond_1
    :goto_0
    sget-object p1, Landroidx/lifecycle/e$a;->ON_DESTROY:Landroidx/lifecycle/e$a;

    .line 23
    .line 24
    if-ne p2, p1, :cond_2

    .line 25
    .line 26
    iget-object p1, p0, Landroidx/fragment/app/FragmentManager$6;->b:Landroidx/lifecycle/e;

    .line 27
    .line 28
    invoke-virtual {p1, p0}, Landroidx/lifecycle/e;->c(Landroidx/lifecycle/i;)V

    .line 29
    .line 30
    .line 31
    invoke-static {v0}, Landroidx/fragment/app/a;->b(Landroidx/fragment/app/a;)Ljava/util/Map;

    .line 32
    .line 33
    .line 34
    move-result-object p1

    .line 35
    iget-object p2, p0, Landroidx/fragment/app/FragmentManager$6;->a:Ljava/lang/String;

    .line 36
    .line 37
    invoke-interface {p1, p2}, Ljava/util/Map;->remove(Ljava/lang/Object;)Ljava/lang/Object;

    .line 38
    .line 39
    .line 40
    :cond_2
    return-void
.end method

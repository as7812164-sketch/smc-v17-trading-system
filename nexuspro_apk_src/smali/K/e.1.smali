.class public abstract LK/e;
.super Lo/r;
.source "SourceFile"


# instance fields
.field private final d:Ljava/util/List;

.field private e:LK/B;


# direct methods
.method public constructor <init>()V
    .locals 1

    .line 1
    invoke-direct {p0}, Lo/r;-><init>()V

    .line 2
    .line 3
    .line 4
    new-instance v0, Ljava/util/ArrayList;

    .line 5
    .line 6
    invoke-direct {v0}, Ljava/util/ArrayList;-><init>()V

    .line 7
    .line 8
    .line 9
    iput-object v0, p0, LK/e;->d:Ljava/util/List;

    .line 10
    .line 11
    new-instance v0, LK/t;

    .line 12
    .line 13
    invoke-direct {v0}, LK/t;-><init>()V

    .line 14
    .line 15
    .line 16
    invoke-virtual {p0, v0}, LK/e;->k(LK/f;)V

    .line 17
    .line 18
    .line 19
    return-void
.end method


# virtual methods
.method public c()Lo/m;
    .locals 3

    .line 1
    iget-object v0, p0, LK/e;->e:LK/B;

    .line 2
    .line 3
    if-nez v0, :cond_0

    .line 4
    .line 5
    new-instance v0, LK/B;

    .line 6
    .line 7
    invoke-direct {v0, p0}, LK/B;-><init>(Landroid/content/Context;)V

    .line 8
    .line 9
    .line 10
    iput-object v0, p0, LK/e;->e:LK/B;

    .line 11
    .line 12
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 13
    .line 14
    .line 15
    move-result-object v0

    .line 16
    invoke-static {v0}, LK/c;->a(Landroid/content/pm/PackageManager;)Z

    .line 17
    .line 18
    .line 19
    move-result v1

    .line 20
    if-eqz v1, :cond_0

    .line 21
    .line 22
    iget-object v1, p0, LK/e;->e:LK/B;

    .line 23
    .line 24
    const-string v2, "org.chromium.arc.payment_app"

    .line 25
    .line 26
    invoke-static {v2, v0}, Lo/j;->a(Ljava/lang/String;Landroid/content/pm/PackageManager;)Lo/j;

    .line 27
    .line 28
    .line 29
    move-result-object v0

    .line 30
    invoke-virtual {v1, v0}, LK/B;->b(Lo/j;)V

    .line 31
    .line 32
    .line 33
    :cond_0
    iget-object v0, p0, LK/e;->e:LK/B;

    .line 34
    .line 35
    return-object v0
.end method

.method public f(Ljava/lang/String;Landroid/os/Bundle;Lo/n;)Landroid/os/Bundle;
    .locals 3

    .line 1
    iget-object v0, p0, LK/e;->d:Ljava/util/List;

    .line 2
    .line 3
    invoke-interface {v0}, Ljava/util/List;->iterator()Ljava/util/Iterator;

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    :cond_0
    invoke-interface {v0}, Ljava/util/Iterator;->hasNext()Z

    .line 8
    .line 9
    .line 10
    move-result v1

    .line 11
    if-eqz v1, :cond_1

    .line 12
    .line 13
    invoke-interface {v0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    .line 14
    .line 15
    .line 16
    move-result-object v1

    .line 17
    check-cast v1, LK/f;

    .line 18
    .line 19
    invoke-interface {v1, p0, p1, p2, p3}, LK/f;->a(Landroid/content/Context;Ljava/lang/String;Landroid/os/Bundle;Lo/n;)Landroid/os/Bundle;

    .line 20
    .line 21
    .line 22
    move-result-object v1

    .line 23
    const-string v2, "success"

    .line 24
    .line 25
    invoke-virtual {v1, v2}, Landroid/os/BaseBundle;->getBoolean(Ljava/lang/String;)Z

    .line 26
    .line 27
    .line 28
    move-result v2

    .line 29
    if-eqz v2, :cond_0

    .line 30
    .line 31
    return-object v1

    .line 32
    :cond_1
    sget-object p1, Landroid/os/Bundle;->EMPTY:Landroid/os/Bundle;

    .line 33
    .line 34
    return-object p1
.end method

.method public k(LK/f;)V
    .locals 1

    .line 1
    iget-object v0, p0, LK/e;->d:Ljava/util/List;

    .line 2
    .line 3
    invoke-interface {v0, p1}, Ljava/util/List;->add(Ljava/lang/Object;)Z

    .line 4
    .line 5
    .line 6
    return-void
.end method

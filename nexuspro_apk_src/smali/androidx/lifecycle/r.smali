.class public Landroidx/lifecycle/r;
.super Landroid/app/Fragment;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Landroidx/lifecycle/r$a;,
        Landroidx/lifecycle/r$b;,
        Landroidx/lifecycle/r$c;
    }
.end annotation


# static fields
.field public static final b:Landroidx/lifecycle/r$b;


# instance fields
.field private a:Landroidx/lifecycle/r$a;


# direct methods
.method static constructor <clinit>()V
    .locals 2

    new-instance v0, Landroidx/lifecycle/r$b;

    const/4 v1, 0x0

    invoke-direct {v0, v1}, Landroidx/lifecycle/r$b;-><init>(LT/b;)V

    sput-object v0, Landroidx/lifecycle/r;->b:Landroidx/lifecycle/r$b;

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    .line 1
    invoke-direct {p0}, Landroid/app/Fragment;-><init>()V

    .line 2
    .line 3
    .line 4
    return-void
.end method

.method private final a(Landroidx/lifecycle/e$a;)V
    .locals 3

    .line 1
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    .line 2
    .line 3
    const/16 v1, 0x1d

    .line 4
    .line 5
    if-ge v0, v1, :cond_0

    .line 6
    .line 7
    sget-object v0, Landroidx/lifecycle/r;->b:Landroidx/lifecycle/r$b;

    .line 8
    .line 9
    invoke-virtual {p0}, Landroid/app/Fragment;->getActivity()Landroid/app/Activity;

    .line 10
    .line 11
    .line 12
    move-result-object v1

    .line 13
    const-string v2, "activity"

    .line 14
    .line 15
    invoke-static {v1, v2}, LT/d;->d(Ljava/lang/Object;Ljava/lang/String;)V

    .line 16
    .line 17
    .line 18
    invoke-virtual {v0, v1, p1}, Landroidx/lifecycle/r$b;->a(Landroid/app/Activity;Landroidx/lifecycle/e$a;)V

    .line 19
    .line 20
    .line 21
    :cond_0
    return-void
.end method

.method private final b(Landroidx/lifecycle/r$a;)V
    .locals 0

    .line 1
    if-eqz p1, :cond_0

    .line 2
    .line 3
    invoke-interface {p1}, Landroidx/lifecycle/r$a;->a()V

    .line 4
    .line 5
    .line 6
    :cond_0
    return-void
.end method

.method private final c(Landroidx/lifecycle/r$a;)V
    .locals 0

    .line 1
    if-eqz p1, :cond_0

    .line 2
    .line 3
    invoke-interface {p1}, Landroidx/lifecycle/r$a;->b()V

    .line 4
    .line 5
    .line 6
    :cond_0
    return-void
.end method

.method private final d(Landroidx/lifecycle/r$a;)V
    .locals 0

    .line 1
    if-eqz p1, :cond_0

    .line 2
    .line 3
    invoke-interface {p1}, Landroidx/lifecycle/r$a;->c()V

    .line 4
    .line 5
    .line 6
    :cond_0
    return-void
.end method


# virtual methods
.method public final e(Landroidx/lifecycle/r$a;)V
    .locals 0

    .line 1
    iput-object p1, p0, Landroidx/lifecycle/r;->a:Landroidx/lifecycle/r$a;

    .line 2
    .line 3
    return-void
.end method

.method public onActivityCreated(Landroid/os/Bundle;)V
    .locals 0

    .line 1
    invoke-super {p0, p1}, Landroid/app/Fragment;->onActivityCreated(Landroid/os/Bundle;)V

    .line 2
    .line 3
    .line 4
    iget-object p1, p0, Landroidx/lifecycle/r;->a:Landroidx/lifecycle/r$a;

    .line 5
    .line 6
    invoke-direct {p0, p1}, Landroidx/lifecycle/r;->b(Landroidx/lifecycle/r$a;)V

    .line 7
    .line 8
    .line 9
    sget-object p1, Landroidx/lifecycle/e$a;->ON_CREATE:Landroidx/lifecycle/e$a;

    .line 10
    .line 11
    invoke-direct {p0, p1}, Landroidx/lifecycle/r;->a(Landroidx/lifecycle/e$a;)V

    .line 12
    .line 13
    .line 14
    return-void
.end method

.method public onDestroy()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Fragment;->onDestroy()V

    .line 2
    .line 3
    .line 4
    sget-object v0, Landroidx/lifecycle/e$a;->ON_DESTROY:Landroidx/lifecycle/e$a;

    .line 5
    .line 6
    invoke-direct {p0, v0}, Landroidx/lifecycle/r;->a(Landroidx/lifecycle/e$a;)V

    .line 7
    .line 8
    .line 9
    const/4 v0, 0x0

    .line 10
    iput-object v0, p0, Landroidx/lifecycle/r;->a:Landroidx/lifecycle/r$a;

    .line 11
    .line 12
    return-void
.end method

.method public onPause()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Fragment;->onPause()V

    .line 2
    .line 3
    .line 4
    sget-object v0, Landroidx/lifecycle/e$a;->ON_PAUSE:Landroidx/lifecycle/e$a;

    .line 5
    .line 6
    invoke-direct {p0, v0}, Landroidx/lifecycle/r;->a(Landroidx/lifecycle/e$a;)V

    .line 7
    .line 8
    .line 9
    return-void
.end method

.method public onResume()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Fragment;->onResume()V

    .line 2
    .line 3
    .line 4
    iget-object v0, p0, Landroidx/lifecycle/r;->a:Landroidx/lifecycle/r$a;

    .line 5
    .line 6
    invoke-direct {p0, v0}, Landroidx/lifecycle/r;->c(Landroidx/lifecycle/r$a;)V

    .line 7
    .line 8
    .line 9
    sget-object v0, Landroidx/lifecycle/e$a;->ON_RESUME:Landroidx/lifecycle/e$a;

    .line 10
    .line 11
    invoke-direct {p0, v0}, Landroidx/lifecycle/r;->a(Landroidx/lifecycle/e$a;)V

    .line 12
    .line 13
    .line 14
    return-void
.end method

.method public onStart()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Fragment;->onStart()V

    .line 2
    .line 3
    .line 4
    iget-object v0, p0, Landroidx/lifecycle/r;->a:Landroidx/lifecycle/r$a;

    .line 5
    .line 6
    invoke-direct {p0, v0}, Landroidx/lifecycle/r;->d(Landroidx/lifecycle/r$a;)V

    .line 7
    .line 8
    .line 9
    sget-object v0, Landroidx/lifecycle/e$a;->ON_START:Landroidx/lifecycle/e$a;

    .line 10
    .line 11
    invoke-direct {p0, v0}, Landroidx/lifecycle/r;->a(Landroidx/lifecycle/e$a;)V

    .line 12
    .line 13
    .line 14
    return-void
.end method

.method public onStop()V
    .locals 1

    .line 1
    invoke-super {p0}, Landroid/app/Fragment;->onStop()V

    .line 2
    .line 3
    .line 4
    sget-object v0, Landroidx/lifecycle/e$a;->ON_STOP:Landroidx/lifecycle/e$a;

    .line 5
    .line 6
    invoke-direct {p0, v0}, Landroidx/lifecycle/r;->a(Landroidx/lifecycle/e$a;)V

    .line 7
    .line 8
    .line 9
    return-void
.end method

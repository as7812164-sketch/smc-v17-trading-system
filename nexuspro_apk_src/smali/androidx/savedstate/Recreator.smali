.class public final Landroidx/savedstate/Recreator;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Landroidx/lifecycle/h;


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Landroidx/savedstate/Recreator$a;
    }
.end annotation


# static fields
.field public static final a:Landroidx/savedstate/Recreator$a;


# direct methods
.method static constructor <clinit>()V
    .locals 2

    new-instance v0, Landroidx/savedstate/Recreator$a;

    const/4 v1, 0x0

    invoke-direct {v0, v1}, Landroidx/savedstate/Recreator$a;-><init>(LT/b;)V

    sput-object v0, Landroidx/savedstate/Recreator;->a:Landroidx/savedstate/Recreator$a;

    return-void
.end method


# virtual methods
.method public h(Landroidx/lifecycle/j;Landroidx/lifecycle/e$a;)V
    .locals 1

    .line 1
    const-string v0, "source"

    .line 2
    .line 3
    invoke-static {p1, v0}, LT/d;->e(Ljava/lang/Object;Ljava/lang/String;)V

    .line 4
    .line 5
    .line 6
    const-string v0, "event"

    .line 7
    .line 8
    invoke-static {p2, v0}, LT/d;->e(Ljava/lang/Object;Ljava/lang/String;)V

    .line 9
    .line 10
    .line 11
    sget-object v0, Landroidx/lifecycle/e$a;->ON_CREATE:Landroidx/lifecycle/e$a;

    .line 12
    .line 13
    if-eq p2, v0, :cond_0

    .line 14
    .line 15
    new-instance p1, Ljava/lang/AssertionError;

    .line 16
    .line 17
    const-string p2, "Next event must be ON_CREATE"

    .line 18
    .line 19
    invoke-direct {p1, p2}, Ljava/lang/AssertionError;-><init>(Ljava/lang/Object;)V

    .line 20
    .line 21
    .line 22
    throw p1

    .line 23
    :cond_0
    invoke-interface {p1}, Landroidx/lifecycle/j;->a()Landroidx/lifecycle/e;

    .line 24
    .line 25
    .line 26
    move-result-object p1

    .line 27
    invoke-virtual {p1, p0}, Landroidx/lifecycle/e;->c(Landroidx/lifecycle/i;)V

    .line 28
    .line 29
    .line 30
    const/4 p1, 0x0

    .line 31
    throw p1
.end method

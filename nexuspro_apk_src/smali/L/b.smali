.class public final synthetic LL/b;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Ljava/lang/Runnable;


# instance fields
.field public final synthetic a:LL/c;

.field public final synthetic b:Ljava/lang/Runnable;


# direct methods
.method public synthetic constructor <init>(LL/c;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, LL/b;->a:LL/c;

    iput-object p2, p0, LL/b;->b:Ljava/lang/Runnable;

    return-void
.end method


# virtual methods
.method public final run()V
    .locals 2

    .line 1
    iget-object v0, p0, LL/b;->a:LL/c;

    iget-object v1, p0, LL/b;->b:Ljava/lang/Runnable;

    invoke-static {v0, v1}, LL/c;->c(LL/c;Ljava/lang/Runnable;)V

    return-void
.end method
